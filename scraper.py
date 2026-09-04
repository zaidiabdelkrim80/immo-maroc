import asyncio
import json
import re
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("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"))


def nettoyer_avec_ia(titre, description, prix_raw, surface_raw):
    """Utilise Groq pour extraire et nettoyer les infos d'une annonce"""
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
        # Nettoyer les balises markdown si présentes
        contenu = re.sub(r'```json|```', '', contenu).strip()
        return json.loads(contenu)
    except Exception as e:
        return None


async def scraper_avito():
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

        print("⏬ Chargement des annonces en cours...")
        for i in range(8):
            await page.evaluate("window.scrollBy(0, 800)")
            await page.wait_for_timeout(800)

        await page.wait_for_timeout(3000)
        print("✅ Page complètement chargée")

        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")

        # Collecter les liens par ID
        liens_par_id = {}
        for lien in soup.find_all("a", href=True):
            href = lien["href"]
            if re.search(r'/appartements/.+_\d+\.htm', href):
                id_match = re.search(r'_(\d+)\.htm', href)
                if id_match:
                    url_complete = href if href.startswith("http") else "https://www.avito.ma" + href
                    liens_par_id[id_match.group(1)] = url_complete

        print(f"🔗 {len(liens_par_id)} liens collectés")

        # Extraire depuis les scripts JSON
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

                # URL
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

            except Exception:
                continue

        print(f"\n🤖 Nettoyage IA de {len(annonces_brutes)} annonces...\n")

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

        # Trier par prix croissant
        annonces.sort(key=lambda x: x.get('prix_dh') or float('inf'))

        print(f"\n📦 {len(annonces)} annonces structurées :\n")
        for a in annonces[:15]:
            print(f"  🏠 {a.get('titre', '')[:60]}")
            print(f"     💰 Prix    : {a['prix_dh']:,} DH" if a.get('prix_dh') else "     💰 Prix    : Non spécifié")
            print(f"     📐 Surface : {a['surface_m2']} m²" if a.get('surface_m2') else "     📐 Surface : Non spécifié")
            print(f"     📊 Prix/m² : {a['prix_m2']:,} DH/m²" if a.get('prix_m2') else "     📊 Prix/m² : -")
            print(f"     🏙️  Ville   : {a['ville']}" if a.get('ville') else "     🏙️  Ville   : Non spécifiée")
            print(f"     🏢 Type    : {a.get('type_bien', '-')}")
            print(f"     🔗 Lien    : {a['url'] if a['url'] else 'Non trouvé'}")
            print()

        # Statistiques
        prix_valides = [a['prix_dh'] for a in annonces if a.get('prix_dh')]
        surface_valides = [a['surface_m2'] for a in annonces if a.get('surface_m2')]
        prix_m2_valides = [a['prix_m2'] for a in annonces if a.get('prix_m2')]

        if prix_valides:
            print("=" * 55)
            print(f"📊 STATISTIQUES MARCHÉ ({len(annonces)} annonces)")
            print(f"   Prix moyen     : {int(sum(prix_valides)/len(prix_valides)):,} DH")
            if surface_valides:
                print(f"   Surface moyenne: {int(sum(surface_valides)/len(surface_valides))} m²")
            if prix_m2_valides:
                print(f"   Prix/m² moyen  : {int(sum(prix_m2_valides)/len(prix_m2_valides)):,} DH/m²")
            print(f"   Annonces avec prix   : {len(prix_valides)}/{len(annonces)}")
            print(f"   Annonces avec surface: {len(surface_valides)}/{len(annonces)}")
            print(f"   Annonces avec lien   : {len([a for a in annonces if a['url']])}/{len(annonces)}")
            print("=" * 55)

        # Sauvegarder
        with open("annonces_propres.json", "w", encoding="utf-8") as f:
            json.dump(annonces, f, ensure_ascii=False, indent=2)

        print(f"\n✅ {len(annonces)} annonces sauvegardées dans annonces_propres.json")
        await browser.close()


asyncio.run(scraper_avito())