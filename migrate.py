import sqlite3
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

SQLITE_PATH = "immo.db"
PG_URL = os.getenv("DATABASE_URL")


def migrer():
    print("🚀 Migration SQLite → Supabase PostgreSQL")
    print("=" * 55)

    # Connexion SQLite
    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()

    # Connexion PostgreSQL
    pg_conn = psycopg2.connect(PG_URL)
    pg_cursor = pg_conn.cursor()

    # ── Migrer les annonces
    print("\n📦 Migration des annonces...")
    sqlite_cursor.execute("SELECT * FROM annonces")
    annonces = sqlite_cursor.fetchall()
    print(f"  {len(annonces)} annonces à migrer")

    nb_ok = 0
    for a in annonces:
        try:
            pg_cursor.execute("""
                INSERT INTO annonces (source, titre, prix_dh, surface_m2, chambres, ville, type_bien, prix_m2, url, date_scraping, actif)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (url) DO NOTHING
            """, (
                a['source'], a['titre'], a['prix_dh'], a['surface_m2'],
                a['chambres'], a['ville'], a['type_bien'], a['prix_m2'],
                a['url'], a['date_scraping'], a['actif']
            ))
            nb_ok += 1
        except Exception as e:
            print(f"  ⚠️ Erreur : {e}")

    pg_conn.commit()
    print(f"  ✅ {nb_ok} annonces migrées")

    # ── Migrer les utilisateurs
    print("\n👤 Migration des utilisateurs...")
    try:
        sqlite_cursor.execute("SELECT * FROM utilisateurs")
        utilisateurs = sqlite_cursor.fetchall()
        print(f"  {len(utilisateurs)} utilisateurs à migrer")

        for u in utilisateurs:
            try:
                pg_cursor.execute("""
                    INSERT INTO utilisateurs (email, password_hash, nom, credits, recherches_gratuites, date_inscription)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (email) DO NOTHING
                """, (
                    u['email'], u['password_hash'], u['nom'],
                    u['credits'], u['recherches_gratuites'], u['date_inscription']
                ))
            except Exception as e:
                print(f"  ⚠️ Erreur : {e}")

        pg_conn.commit()
        print(f"  ✅ {len(utilisateurs)} utilisateurs migrés")
    except Exception as e:
        print(f"  ⚠️ Table utilisateurs : {e}")

    # ── Stats finales
    pg_cursor.execute("SELECT COUNT(*) FROM annonces")
    total = pg_cursor.fetchone()[0]
    print(f"\n✅ Migration terminée — {total} annonces dans Supabase !")

    sqlite_conn.close()
    pg_conn.close()


if __name__ == "__main__":
    migrer()