import os
from datetime import datetime
from db_config import get_db_connection, get_placeholder

DB_PATH = "immo.db"


def init_db():
    from db_config import init_tables
    init_tables()
    print("✅ Base de données initialisée")


def sauvegarder_annonce(annonce, source="avito"):
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    ph = get_placeholder(db_type)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    url = annonce.get("url", "")

    try:
        cursor.execute(f"SELECT id, prix_dh FROM annonces WHERE url = {ph}", (url,))
        existante = cursor.fetchone()

        if existante:
            ancien_prix = existante[1]
            nouveau_prix = annonce.get("prix_dh")
            if nouveau_prix and ancien_prix != nouveau_prix:
                cursor.execute(f"""
                    INSERT INTO historique_prix (url, prix_dh, date_observation)
                    VALUES ({ph}, {ph}, {ph})
                """, (url, nouveau_prix, now))
                cursor.execute(f"""
                    UPDATE annonces SET prix_dh = {ph}, prix_m2 = {ph}, date_scraping = {ph}
                    WHERE url = {ph}
                """, (nouveau_prix, annonce.get("prix_m2"), now, url))
        else:
            cursor.execute(f"""
                INSERT INTO annonces (source, titre, prix_dh, surface_m2, chambres, ville, type_bien, prix_m2, url, date_scraping)
                VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
                ON CONFLICT (url) DO NOTHING
            """, (
                source, annonce.get("titre"), annonce.get("prix_dh"),
                annonce.get("surface_m2"), annonce.get("chambres"),
                annonce.get("ville"), annonce.get("type_bien"),
                annonce.get("prix_m2"), url, now
            ))

        conn.commit()
    except Exception as e:
        print(f"⚠️ Erreur sauvegarde : {e}")
        conn.rollback()
    finally:
        conn.close()


def sauvegarder_annonces(annonces, source="avito"):
    nb = 0
    for a in annonces:
        if a.get("url"):
            sauvegarder_annonce(a, source)
            nb += 1
    return nb


def stats_db():
    conn, db_type = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM annonces")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM annonces WHERE prix_dh IS NOT NULL")
    avec_prix = cursor.fetchone()[0]

    cursor.execute("SELECT AVG(prix_dh) FROM annonces WHERE prix_dh IS NOT NULL")
    prix_moyen = cursor.fetchone()[0]

    cursor.execute("SELECT ville, COUNT(*) as nb FROM annonces WHERE ville IS NOT NULL GROUP BY ville ORDER BY nb DESC LIMIT 5")
    top_villes = cursor.fetchall()

    cursor.execute("SELECT source, COUNT(*) as nb FROM annonces GROUP BY source")
    par_source = cursor.fetchall()

    conn.close()

    print("\n" + "=" * 55)
    print("📊 STATISTIQUES BASE DE DONNÉES")
    print(f"   Total annonces    : {total}")
    print(f"   Avec prix         : {avec_prix}")
    print(f"   Prix moyen        : {int(prix_moyen):,} DH" if prix_moyen else "   Prix moyen        : -")
    print(f"\n   📍 Top villes :")
    for ville, nb in top_villes:
        print(f"      {ville} : {nb} annonces")
    print(f"\n   🌐 Par source :")
    for source, nb in par_source:
        print(f"      {source} : {nb} annonces")
    print("=" * 55)