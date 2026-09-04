import asyncio
import json
import re
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from groq import Groq
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from database import init_db, sauvegarder_annonces, stats_db
from scrapers.mubawab import scraper_mubawab
from scrapers.yakeey import scraper_yakeey

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def nettoyer_avec_ia(titre, description, prix_raw, surface_raw):
    prompt = f"""Tu es un assistant qui extrait des données immobilières marocaines.
Voici les informations brutes d'une annonce :
- Titre : {titre}
- Description : {description[:300] if description else 'Non disponible'}
- Prix brut : {prix_raw}
- Surface brute : {surface_raw}

Réponds UNIQUEMENT en JSON valide, sans texte avant ou après, sans balises markdown :
{{
  "titre": "titre propre et lisible",
  "prix_dh": null ou nombre entier (prix en DH, entre 100000 et 50000000),
  "surface_m2": null ou nombre entier (surface en m², entre 20 et 1000),
  "chambres": null ou nombre entier,
  "ville": null ou nom de ville marocaine,
  "type_bien": "appartement ou studio ou duplex ou penthouse"
}}"""

    try:
        response = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=300,
        )
        contenu = response.choices[0].message.content.strip()
        contenu = re.sub(r'```json|```', '', contenu).strip()
        contenu = re.sub(r'<think>.*?</think>', '', contenu, flags=re.DOTALL).strip()
        return json.loads(contenu)
    except Exception as e:
        print(f"    ⚠️ Erreur IA : {e}")
        return None


async def scraper_avito():
    print("\n" + "=" * 55)
    print("🏠 SCRAPER AVITO.MA")
    print("=" * 55)

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

        print("🔍 Connexion à Avito.ma...")
        await page.goto(
            "https://www.avito.ma/fr/maroc/appartements-%C3%A0_vendre",
            wait_until="domcontentloaded",
            timeout=60000
        )
        await page.wait_for_timeout(5000)

        print("⏬ Chargement des annonces...")
        for i in range(8):
            await page.evaluate("window.scrollBy(0, 800)")
            await page.wait_for_timeout(800)
        await page.wait_for_timeout(3000)
        print("✅ Page chargée")

        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")

        liens_par_id = {}
        for lien in soup.find_all("a", href=True):
            href = lien["href"]
            if re.search(r'/appartements/.+_\d+\.htm', href):
                id_match = re.search(r'_(\d+)\.htm', href)
                if id_match:
                    url_complete = href if href.startswith("http") else "https://www.avito.ma" + href
                    liens_par_id[id_match.group(1)] = url_complete

        annonces_brutes = []
        scripts = soup.find_all("script", type="application/ld+json")

        for script in scripts:
            try:
                data = json.loads(script.string)
                if not isinstance(data, dict) or "name" not in data:
                    continue
                titre = data.get("name", "")
                description = data.get("description", "")
                offers = data.get("offers", {})
                prix_raw = offers.get("price", "") if isinstance(offers, dict) else ""
                surface_raw = ""
                surface_match = re.search(r'(\d+)\s*m[²2]', titre + " " + description, re.IGNORECASE)
                if surface_match:
                    surface_raw = surface_match.group(0)

                url = ""
                json_str = json.dumps(data)
                id_matches = re.findall(r'_(\d{7,9})(?:\.htm|")', json_str)
                for id_trouve in id_matches:
                    if id_trouve in liens_par_id:
                        url = liens_par_id[id_trouve]
                        break
                if not url:
                    product_id = str(data.get("productID", data.get("sku", "")))
                    if product_id in liens_par_id:
                        url = liens_par_id[product_id]

                annonces_brutes.append({
                    "titre": titre,
                    "description": description,
                    "prix_raw": prix_raw,
                    "surface_raw": surface_raw,
                    "url": url
                })
            except:
                continue

        print(f"\n🤖 Nettoyage IA de {len(annonces_brutes)} annonces Avito...\n")

        annonces = []
        for i, a in enumerate(annonces_brutes):
            print(f"  ⚙️  Annonce {i+1}/{len(annonces_brutes)} : {a['titre'][:40]}...")
            infos = nettoyer_avec_ia(a['titre'], a['description'], a['prix_raw'], a['surface_raw'])
            if infos:
                prix_m2 = None
                if infos.get('prix_dh') and infos.get('surface_m2'):
                    try:
                        prix_m2 = round(infos['prix_dh'] / infos['surface_m2'])
                    except:
                        pass
                infos['prix_m2'] = prix_m2
                infos['url'] = a['url']
                annonces.append(infos)

        await browser.close()
        print(f"\n✅ {len(annonces)} annonces Avito extraites")
        return annonces


async def main():
    debut = datetime.now()
    print(f"\n🚀 DÉMARRAGE SCRAPING — {debut.strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 55)

    init_db()

    # ── Avito
    try:
        annonces_avito = await scraper_avito()
        nb_avito = sauvegarder_annonces(annonces_avito, source="avito")
        print(f"💾 {nb_avito} annonces Avito sauvegardées")
    except Exception as e:
        print(f"❌ Erreur Avito : {e}")
        annonces_avito = []

    # ── Mubawab
    try:
        annonces_mubawab = await scraper_mubawab()
        nb_mubawab = sauvegarder_annonces(annonces_mubawab, source="mubawab")
        print(f"💾 {nb_mubawab} annonces Mubawab sauvegardées")
    except Exception as e:
        print(f"❌ Erreur Mubawab : {e}")
        annonces_mubawab = []

    # ── Yakeey
    try:
        annonces_yakeey = await scraper_yakeey(nb_pages=5)
        nb_yakeey = sauvegarder_annonces(annonces_yakeey, source="yakeey")
        print(f"💾 {nb_yakeey} annonces Yakeey sauvegardées")
    except Exception as e:
        print(f"❌ Erreur Yakeey : {e}")
        annonces_yakeey = []

    # ── Résumé
    fin = datetime.now()
    duree = (fin - debut).seconds
    total = len(annonces_avito) + len(annonces_mubawab) + len(annonces_yakeey)

    print("\n" + "=" * 55)
    print(f"✅ SCRAPING TERMINÉ en {duree}s")
    print(f"   Avito   : {len(annonces_avito)} annonces")
    print(f"   Mubawab : {len(annonces_mubawab)} annonces")
    print(f"   Yakeey  : {len(annonces_yakeey)} annonces")
    print(f"   Total   : {total} annonces")
    print("=" * 55)

    stats_db()


asyncio.run(main())