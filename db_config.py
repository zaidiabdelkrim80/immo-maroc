import os
import sqlite3
from dotenv import load_dotenv
load_dotenv()
# Détecter si on est sur Streamlit Cloud ou en local
def get_db_connection():
    """Retourne une connexion à la bonne BDD selon l'environnement"""
    db_url = ""

    # Essai 1 : Streamlit secrets
    try:
        import streamlit as st
        db_url = st.secrets.get("DATABASE_URL", "")
    except:
        pass

    # Essai 2 : variable d'environnement
    if not db_url:
        db_url = os.environ.get("DATABASE_URL", "")

    # Essai 3 : .env local
    if not db_url:
        try:
            from dotenv import load_dotenv
            load_dotenv()
            db_url = os.environ.get("DATABASE_URL", "")
        except:
            pass

    if db_url and "postgresql" in db_url:
        import psycopg2
        conn = psycopg2.connect(db_url)
        return conn, "postgresql"
    else:
        conn = sqlite3.connect("immo.db")
        return conn, "sqlite"


def init_tables():
    """Crée les tables si elles n'existent pas"""
    conn, db_type = get_db_connection()
    cursor = conn.cursor()

    if db_type == "postgresql":
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS annonces (
                id SERIAL PRIMARY KEY,
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
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS utilisateurs (
                id SERIAL PRIMARY KEY,
                email TEXT UNIQUE,
                password_hash TEXT,
                nom TEXT,
                provider TEXT DEFAULT 'email',
                credits INTEGER DEFAULT 5,
                recherches_gratuites INTEGER DEFAULT 5,
                est_payant INTEGER DEFAULT 0,
                date_inscription TEXT,
                derniere_connexion TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions_anonymes (
                session_id TEXT PRIMARY KEY,
                recherches_restantes INTEGER DEFAULT 5,
                date_creation TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historique_recherches (
                id SERIAL PRIMARY KEY,
                email TEXT,
                session_id TEXT,
                ville TEXT,
                budget_max INTEGER,
                surface_min INTEGER,
                date_recherche TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historique_prix (
                id SERIAL PRIMARY KEY,
                url TEXT,
                prix_dh INTEGER,
                date_observation TEXT
            )
        """)
    else:
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
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS utilisateurs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE,
                password_hash TEXT,
                nom TEXT,
                provider TEXT DEFAULT 'email',
                credits INTEGER DEFAULT 5,
                recherches_gratuites INTEGER DEFAULT 5,
                est_payant INTEGER DEFAULT 0,
                date_inscription TEXT,
                derniere_connexion TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions_anonymes (
                session_id TEXT PRIMARY KEY,
                recherches_restantes INTEGER DEFAULT 5,
                date_creation TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historique_recherches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT,
                session_id TEXT,
                ville TEXT,
                budget_max INTEGER,
                surface_min INTEGER,
                date_recherche TEXT
            )
        """)
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
    print("✅ Tables initialisées")


def get_placeholder(db_type):
    """Retourne le bon placeholder selon la BDD"""
    return "%s" if db_type == "postgresql" else "?"


if __name__ == "__main__":
    init_tables()
    conn, db_type = get_db_connection()
    print(f"✅ Connecté à : {db_type}")
    conn.close()