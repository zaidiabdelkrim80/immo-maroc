import asyncio
import re
import json
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
    'Oulfa', 'Hivernage', 'Maarif', 'Hay Hassani', 'Ain Chock',
    'Sidi Maarouf', 'Palmier', 'Agdal', 'Californie', 'Mhamid',
    'Belvédère', 'Ain Diab', 'Dar Bouazza', 'Hay Riad', 'Errahma',
    'Anfa', 'Mohammedia', 'Mohammédia'
]


def extraire_ville(texte):
    for ville in VILLES_MAROC:
        if ville.lower() in texte.lower():
            return ville
    return None


def extraire_prix(texte):
    texte_propre = re.sub(r'[\d\s\u202f\xa0]+\s*(?:DH|MAD)\s*/\s*mois', '', texte, flags=re.IGNORECASE)
    matches = re.findall(r'([\d][\d\u202f\xa0\s]{2,})\s*(?:DH|MAD)', texte_propre, re.IGNORECASE)
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


async def scraper_yakeey(nb_pages=5):
    print("\n" + "=" * 55)
    print("🏠 SCRAPER YAKEEY.COM")
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

        cartes_traitees = set()

        for num_page in range(1, nb_pages + 1):
            url_page = f"https://yakeey.com/fr-ma/achat/biens/maroc?page={num_page}"
            print(f"\n🔍 Page {num_page}/{nb_pages} : {url_page}")

            try:
                await page.goto(url_page, wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_timeout(4000)

                for i in range(6):
                    await page.evaluate("window.scrollBy(0, 800)")
                    await page.wait_for_timeout(600)
                await page.wait_for_timeout(2000)

                html = await page.content()
                soup = BeautifulSoup(html, "html.parser")

                # Extraire annonces de cette page
                elements_dh = soup.find_all(string=re.compile(r'^\s*[\d\s\u202f]+\s*DH\s*$'))
                nb_avant = len(annonces)

                for el in elements_dh:
                    prix_texte = el.strip()
                    prix = extraire_prix(prix_texte)
                    if not prix:
                        continue

                    noeud = el.parent
                    carte = None
                    for _ in range(6):
                        if noeud is None:
                            break
                        texte_noeud = noeud.get_text(strip=True)
                        if len(texte_noeud) > 30 and any(v.lower() in texte_noeud.lower() for v in VILLES_MAROC):
                            carte = noeud
                            break
                        noeud = noeud.parent

                    if not carte:
                        continue

                    texte = carte.get_text(separator=" ", strip=True)
                    cle = texte[:60]
                    if cle in cartes_traitees:
                        continue
                    cartes_traitees.add(cle)

                    surface = extraire_surface(texte)
                    chambres = None
                    ch_match = re.search(r'(\d+)\s*chambre', texte, re.IGNORECASE)
                    if ch_match:
                        chambres = int(ch_match.group(1))

                    ville = extraire_ville(texte)

                    type_bien = "appartement"
                    texte_lower = texte.lower()
                    if "villa" in texte_lower:
                        type_bien = "villa"
                    elif "studio" in texte_lower:
                        type_bien = "studio"
                    elif "terrain" in texte_lower:
                        type_bien = "terrain"
                    elif "bureau" in texte_lower:
                        type_bien = "bureau"

                    titre = f"{type_bien.capitalize()} à vendre"
                    if ville:
                        titre += f" à {ville}"
                    if surface:
                        titre += f" {surface} m²"

                    lien_tag = carte.find("a", href=True)
                    url_annonce = ""
                    if lien_tag:
                        href = lien_tag["href"]
                        url_annonce = href if href.startswith("http") else "https://yakeey.com" + href

                    prix_m2 = round(prix / surface) if prix and surface else None

                    annonces.append({
                        "titre": titre,
                        "prix_dh": prix,
                        "surface_m2": surface,
                        "chambres": chambres,
                        "ville": ville,
                        "prix_m2": prix_m2,
                        "type_bien": type_bien,
                        "url": url_annonce
                    })

                print(f"  ✅ {len(annonces) - nb_avant} annonces extraites sur cette page")
                await page.wait_for_timeout(2000)  # Pause anti-ban

            except Exception as e:
                print(f"  ❌ Erreur page {num_page} : {e}")
                continue

        await browser.close()

    print(f"\n📦 {len(annonces)} annonces Yakeey extraites au total")
    return annonces


if __name__ == "__main__":
    annonces = asyncio.run(scraper_yakeey())
    print("\n" + "=" * 55)
    for a in annonces[:5]:
        print(f"\n🏠 {a['titre']}")
        print(f"   💰 {a['prix_dh']:,} DH | 📐 {a['surface_m2']} m² | 🏙️ {a['ville']}")