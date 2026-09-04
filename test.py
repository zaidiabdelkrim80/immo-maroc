import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()
url = os.getenv("DATABASE_URL")
print(f"URL : {url[:50]}...")

try:
    conn = psycopg2.connect(url)
    print("✅ Connexion OK !")
    conn.close()
except Exception as e:
    print(f"❌ Erreur : {e}")