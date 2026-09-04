import asyncio
import re
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

load_dotenv()

VILLES_MAROC = [
    'Casablanca', 'Rabat', 'Marrakech', 'Fès', 'Tanger', 'Agadir',
    'Meknès', 'Oujda', 'Kénitra', 'Tétouan', 'Salé', 'Nador',
    'Mohammedia', 'El Jadida', 'Béni Mellal', 'Settat', 'Temara',
    'Bouznika', 'Guéliz', 'Ain Sebaa', 'Bouskoura', 'Tamesna',
    'Oulfa', 'Hivernage', 'Bournazil', 'Prestigia', 'Maarif',
    'Hay Hassani', 'Ain Chock', 'Sidi Maarouf', 'Palmier', 'Agdal',
    'Californie', 'Mhamid', 'Belvédère'
]


def extraire_ville(texte):
    for ville in VILLES_MAROC:
        if ville.lower() in texte.lower():
            return ville
    return None


def extraire_prix(texte):
    texte = re.sub(r'[\d\s\u202f\xa0]+\s*(?:DH|MAD)\s*/\s*mois', '', texte, flags=re.IGNORECASE)
    matches = re.findall(r'([\d][\d\u202f\xa0\s]{2,})\s*(?:DH|MAD)', texte, re.IGNORECASE)
    for m in matches:
        prix_str = re.sub(r'[\s\u202f\xa0]', '', m)
        try:
            prix = int(prix_str)
            if 100000 <= prix <= 15000000:
                return prix
        except:
            continue
    return None


def extraire_surface(texte):
    match = re.search(r'(\d+)\s*m[²2]', texte, re.IGNORECASE)
    if match:
        s = int(match.group(1))
        if 20 <= s <= 1000:
            return s
    return None


async def extraire_details_annonce(page, url):
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(2000)

        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")

        # Titre
        titre = ""
        meta_titre = soup.find("meta", property="og:title")
        if meta_titre:
            titre = meta_titre.get("content", "")[:80]
        if not titre:
            title_tag = soup.find("title")
            if title_tag:
                titre = title_tag.get_text(strip=True)[:80]
                titre = re.sub(r'\s*[\|\-]\s*Mubawab.*', '', titre).strip()

        texte = soup.get_text(separator=" ", strip=True)

        # Prix
        prix = None
        meta_prix = soup.find("meta", property="og:price:amount") or \
                    soup.find("meta", attrs={"name": "price"})
        if meta_prix:
            try:
                prix = int(float(meta_prix.get("content", "0").replace(" ", "")))
                if not (100000 <= prix <= 15000000):
                    prix = None
            except:
                prix = None

        if not prix:
            for tag in soup.find_all(["span", "div", "strong", "p"],
                                      class_=re.compile(r'price|prix|cost', re.I)):
                t = tag.get_text(strip=True)
                p = extraire_prix(t)
                if p:
                    prix = p
                    break

        if not prix:
            prix = extraire_prix(texte)

        # Surface
        surface = extraire_surface(texte)

        # Chambres
        chambres_match = re.search(r'(\d+)\s*chambre', texte)
        chambres = int(chambres_match.group(1)) if chambres_match else None

        # Ville
        ville = extraire_ville(url + " " + texte)

        # Type bien
        type_bien = "appartement"
        texte_lower = texte.lower()
        if "villa" in texte_lower:
            type_bien = "villa"
        elif "studio" in texte_lower:
            type_bien = "studio"
        elif "terrain" in texte_lower:
            type_bien = "terrain"

        prix_m2 = round(prix / surface) if prix and surface else None

        return {
            "titre": titre,
            "prix_dh": prix,
            "surface_m2": surface,
            "chambres": chambres,
            "ville": ville,
            "prix_m2": prix_m2,
            "type_bien": type_bien,
            "url": url
        }

    except Exception as e:
        print(f"    ⚠️ Erreur : {e}")
        return None


async def scraper_mubawab():
    print("\n" + "=" * 55)
    print("🏠 SCRAPER MUBAWAB.MA")
    print("=" * 55)

    annonces = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )

        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
            locale="fr-MA",
        )

        page = await context.new_page()
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        print("🔍 Collecte des liens annonces...")
        await page.goto(
            "https://www.mubawab.ma/fr/sc/appartements-a-vendre",
            wait_until="domcontentloaded",
            timeout=60000
        )
        await page.wait_for_timeout(5000)

        for i in range(6):
            await page.evaluate("window.scrollBy(0, 800)")
            await page.wait_for_timeout(800)
        await page.wait_for_timeout(2000)

        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")

        seen = set()
        liens = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if re.search(r'/fr/pa/\d+/', href) and href not in seen:
                seen.add(href)
                url = href if href.startswith("http") else "https://www.mubawab.ma" + href
                liens.append(url)

        print(f"✅ {len(liens)} liens collectés")

        print(f"\n🔍 Extraction des détails (max 15 annonces)...")
        for i, url in enumerate(liens[:15]):
            print(f"  ⚙️  Annonce {i+1}/{min(len(liens), 15)} : {url.split('/')[-1][:40]}...")
            infos = await extraire_details_annonce(page, url)
            if infos:
                annonces.append(infos)
                print(f"     ✅ Prix: {infos['prix_dh']} DH | Surface: {infos['surface_m2']} m² | Ville: {infos['ville']}")
            await page.wait_for_timeout(1000)

        await browser.close()

    print(f"\n📦 {len(annonces)} annonces Mubawab extraites")
    print("\n" + "=" * 55)
    for a in annonces[:5]:
        print(f"\n🏠 {a['titre'][:55]}")
        print(f"   💰 {a['prix_dh']} DH | 📐 {a['surface_m2']} m² | 🏙️ {a['ville']}")

    return annonces


if __name__ == "__main__":
    asyncio.run(scraper_mubawab())