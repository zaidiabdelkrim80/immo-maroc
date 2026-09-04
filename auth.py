import sqlite3
import hashlib
from datetime import datetime

DB_PATH = "immo.db"


def init_auth_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

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

    conn.commit()
    conn.close()


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def inscrire_utilisateur(email, password, nom):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO utilisateurs (email, password_hash, nom, credits, recherches_gratuites, date_inscription)
            VALUES (?, ?, ?, 5, 5, ?)
        """, (email, hash_password(password), nom, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        return True, "✅ Compte créé avec succès !"
    except sqlite3.IntegrityError:
        return False, "❌ Cet email est déjà utilisé."
    finally:
        conn.close()


def connecter_utilisateur(email, password):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM utilisateurs WHERE email = ? AND password_hash = ?
    """, (email, hash_password(password)))
    user = cursor.fetchone()
    if user:
        cursor.execute("""
            UPDATE utilisateurs SET derniere_connexion = ? WHERE email = ?
        """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), email))
        conn.commit()
    conn.close()
    return user


def get_user(email):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM utilisateurs WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    return user


def get_credits(email):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT credits FROM utilisateurs WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0


def utiliser_credit(email):
    credits = get_credits(email)
    if credits <= 0:
        return False
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE utilisateurs SET credits = credits - 1 WHERE email = ?", (email,))
    conn.commit()
    conn.close()
    return True


def ajouter_credits(email, nb):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE utilisateurs SET credits = credits + ? WHERE email = ?", (nb, email))
    conn.commit()
    conn.close()


def get_session_anonyme(session_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sessions_anonymes WHERE session_id = ?", (session_id,))
    session = cursor.fetchone()
    if not session:
        cursor.execute("""
            INSERT INTO sessions_anonymes (session_id, recherches_restantes, date_creation)
            VALUES (?, 5, ?)
        """, (session_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        cursor.execute("SELECT * FROM sessions_anonymes WHERE session_id = ?", (session_id,))
        session = cursor.fetchone()
    conn.close()
    return session


def utiliser_recherche_anonyme(session_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT recherches_restantes FROM sessions_anonymes WHERE session_id = ?", (session_id,))
    row = cursor.fetchone()
    if not row or row[0] <= 0:
        conn.close()
        return False
    cursor.execute("""
        UPDATE sessions_anonymes SET recherches_restantes = recherches_restantes - 1
        WHERE session_id = ?
    """, (session_id,))
    conn.commit()
    conn.close()
    return True


def enregistrer_recherche(email=None, session_id=None, ville=None, budget_max=None, surface_min=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO historique_recherches (email, session_id, ville, budget_max, surface_min, date_recherche)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (email, session_id, ville, budget_max, surface_min, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_auth_db()
    print("✅ Base auth initialisée")