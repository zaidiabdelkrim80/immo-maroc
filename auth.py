import hashlib
from datetime import datetime
from db_config import get_db_connection, get_placeholder


def init_auth_db():
    from db_config import init_tables
    init_tables()


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def inscrire_utilisateur(email, password, nom):
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    ph = get_placeholder(db_type)
    try:
        cursor.execute(f"""
            INSERT INTO utilisateurs (email, password_hash, nom, credits, recherches_gratuites, date_inscription)
            VALUES ({ph}, {ph}, {ph}, 5, 5, {ph})
        """, (email, hash_password(password), nom, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        return True, "✅ Compte créé avec succès !"
    except Exception as e:
        conn.rollback()
        return False, "❌ Cet email est déjà utilisé."
    finally:
        conn.close()


def connecter_utilisateur(email, password):
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    ph = get_placeholder(db_type)
    cursor.execute(f"""
        SELECT * FROM utilisateurs WHERE email = {ph} AND password_hash = {ph}
    """, (email, hash_password(password)))
    user = cursor.fetchone()
    if user:
        cursor.execute(f"""
            UPDATE utilisateurs SET derniere_connexion = {ph} WHERE email = {ph}
        """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), email))
        conn.commit()
    conn.close()
    return user


def get_credits(email):
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    ph = get_placeholder(db_type)
    cursor.execute(f"SELECT credits FROM utilisateurs WHERE email = {ph}", (email,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0


def utiliser_credit(email):
    credits = get_credits(email)
    if credits <= 0:
        return False
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    ph = get_placeholder(db_type)
    cursor.execute(f"UPDATE utilisateurs SET credits = credits - 1 WHERE email = {ph}", (email,))
    conn.commit()
    conn.close()
    return True


def ajouter_credits(email, nb):
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    ph = get_placeholder(db_type)
    cursor.execute(f"UPDATE utilisateurs SET credits = credits + {ph} WHERE email = {ph}", (nb, email))
    conn.commit()
    conn.close()


def get_session_anonyme(session_id):
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    ph = get_placeholder(db_type)
    cursor.execute(f"SELECT * FROM sessions_anonymes WHERE session_id = {ph}", (session_id,))
    session = cursor.fetchone()
    if not session:
        cursor.execute(f"""
            INSERT INTO sessions_anonymes (session_id, recherches_restantes, date_creation)
            VALUES ({ph}, 5, {ph})
            ON CONFLICT (session_id) DO NOTHING
        """, (session_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        cursor.execute(f"SELECT * FROM sessions_anonymes WHERE session_id = {ph}", (session_id,))
        session = cursor.fetchone()
    conn.close()
    return session


def utiliser_recherche_anonyme(session_id):
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    ph = get_placeholder(db_type)
    cursor.execute(f"SELECT recherches_restantes FROM sessions_anonymes WHERE session_id = {ph}", (session_id,))
    row = cursor.fetchone()
    if not row or row[0] <= 0:
        conn.close()
        return False
    cursor.execute(f"""
        UPDATE sessions_anonymes SET recherches_restantes = recherches_restantes - 1
        WHERE session_id = {ph}
    """, (session_id,))
    conn.commit()
    conn.close()
    return True


def enregistrer_recherche(email=None, session_id=None, ville=None, budget_max=None, surface_min=None):
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    ph = get_placeholder(db_type)
    cursor.execute(f"""
        INSERT INTO historique_recherches (email, session_id, ville, budget_max, surface_min, date_recherche)
        VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph})
    """, (email, session_id, ville, budget_max, surface_min, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_auth_db()
    print("✅ Base auth initialisée")