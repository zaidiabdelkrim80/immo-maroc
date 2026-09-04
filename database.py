import sqlite3
import os
from datetime import datetime


DB_PATH = "immo.db"


def init_db():
    """Crée la base de données et la table annonces si elles n'existent pas"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS annonces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            titre TEXT,
            prix_dh INTEGER,
            surface_m2 INTEGER,
            chambres INTEGER,
            ville TEXT,
            type_bien TEXT,
            prix_m2 INTEGER,
            url TEXT UNIQUE,
            date_scraping TEXT,
            actif INTEGER DEFAULT 1
        )
    """)

    # Table historique des prix
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historique_prix (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT,
            prix_dh INTEGER,
            date_observation TEXT
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Base de données initialisée")


def sauvegarder_annonce(annonce, source="avito"):
    """Sauvegarde une annonce — ignore si l'URL existe déjà, met à jour le prix si changé"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    url = annonce.get("url", "")

    # Vérifier si l'annonce existe déjà
    cursor.execute("SELECT id, prix_dh FROM annonces WHERE url = ?", (url,))
    existante = cursor.fetchone()

    if existante:
        ancien_prix = existante[1]
        nouveau_prix = annonce.get("prix_dh")

        # Si le prix a changé, on le note dans l'historique
        if nouveau_prix and ancien_prix != nouveau_prix:
            cursor.execute("""
                INSERT INTO historique_prix (url, prix_dh, date_observation)
                VALUES (?, ?, ?)
            """, (url, nouveau_prix, now))
            cursor.execute("""
                UPDATE annonces SET prix_dh = ?, prix_m2 = ?, date_scraping = ?
                WHERE url = ?
            """, (nouveau_prix, annonce.get("prix_m2"), now, url))
            print(f"  📈 Prix mis à jour : {ancien_prix:,} → {nouveau_prix:,} DH")

    else:
        # Nouvelle annonce
        cursor.execute("""
            INSERT INTO annonces (source, titre, prix_dh, surface_m2, chambres, ville, type_bien, prix_m2, url, date_scraping)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            source,
            annonce.get("titre"),
            annonce.get("prix_dh"),
            annonce.get("surface_m2"),
            annonce.get("chambres"),
            annonce.get("ville"),
            annonce.get("type_bien"),
            annonce.get("prix_m2"),
            url,
            now
        ))

    conn.commit()
    conn.close()


def sauvegarder_annonces(annonces, source="avito"):
    """Sauvegarde une liste d'annonces"""
    nouvelles = 0
    for a in annonces:
        if a.get("url"):
            sauvegarder_annonce(a, source)
            nouvelles += 1
    return nouvelles


def stats_db():
    """Affiche les statistiques de la base de données"""
    conn = sqlite3.connect(DB_PATH)
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


if __name__ == "__main__":
    init_db()
    stats_db()