import schedule
import time
import asyncio
import logging
from datetime import datetime
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s — %(levelname)s — %(message)s',
    handlers=[
        logging.FileHandler("scraping.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

# Flag pour éviter les lancements simultanés
scraping_en_cours = False


def lancer_scraping():
    global scraping_en_cours
    if scraping_en_cours:
        log.info("⏳ Scraping déjà en cours — ignoré")
        return

    scraping_en_cours = True
    log.info("🚀 DÉMARRAGE SCRAPING AUTOMATIQUE")
    try:
        from main import main
        asyncio.run(main())
        log.info("✅ SCRAPING TERMINÉ AVEC SUCCÈS")
    except Exception as e:
        log.error(f"❌ ERREUR SCRAPING : {e}")
    finally:
        scraping_en_cours = False
        prochain = schedule.next_run()
        if prochain:
            log.info(f"⏰ Prochain scraping : {prochain.strftime('%d/%m/%Y à %H:%M:%S')}")


log.info("=" * 55)
log.info("🤖 SCHEDULER IMMO MAROC DÉMARRÉ")
log.info("=" * 55)

# Scraping tous les jours à 06:00
schedule.every().day.at("06:00").do(lancer_scraping)

log.info("📅 Planning : scraping tous les jours à 06:00")
log.info(f"⏰ Prochain scraping : {schedule.next_run().strftime('%d/%m/%Y à %H:%M:%S')}")
log.info("💡 Pour arrêter : Ctrl+C")
log.info("=" * 55)

# Premier scraping immédiat au démarrage (une seule fois)
log.info("🔄 Premier scraping au démarrage...")
lancer_scraping()

# Boucle principale
while True:
    try:
        schedule.run_pending()
        time.sleep(60)
    except KeyboardInterrupt:
        log.info("\n⛔ Scheduler arrêté manuellement")
        break
    except Exception as e:
        log.error(f"❌ Erreur : {e}")
        time.sleep(60)