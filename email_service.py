import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import secrets
import hashlib
from datetime import datetime, timedelta
from db_config import get_db_connection, get_placeholder


def get_sendgrid_key():
    try:
        import streamlit as st
        return st.secrets.get("SENDGRID_API_KEY", os.getenv("SENDGRID_API_KEY", ""))
    except:
        return os.getenv("SENDGRID_API_KEY", "")


def get_from_email():
    try:
        import streamlit as st
        return st.secrets.get("SENDGRID_FROM_EMAIL", os.getenv("SENDGRID_FROM_EMAIL", ""))
    except:
        return os.getenv("SENDGRID_FROM_EMAIL", "")


def init_reset_table():
    """Crée la table pour les tokens de reset"""
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    ph = get_placeholder(db_type)

    if db_type == "postgresql":
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reset_tokens (
                id SERIAL PRIMARY KEY,
                email TEXT NOT NULL,
                token TEXT UNIQUE NOT NULL,
                expires_at TEXT NOT NULL,
                used INTEGER DEFAULT 0
            )
        """)
    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reset_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                token TEXT UNIQUE NOT NULL,
                expires_at TEXT NOT NULL,
                used INTEGER DEFAULT 0
            )
        """)

    conn.commit()
    conn.close()


def envoyer_email_reset(email, base_url="https://maghreb-immo.streamlit.app"):
    """Génère un token de reset et envoie l'email"""
    # Générer token sécurisé
    token = secrets.token_urlsafe(32)
    expires_at = (datetime.now() + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")

    # Sauvegarder en BDD
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    ph = get_placeholder(db_type)

    cursor.execute(f"""
        INSERT INTO reset_tokens (email, token, expires_at)
        VALUES ({ph}, {ph}, {ph})
    """, (email, token, expires_at))
    conn.commit()
    conn.close()

    # Construire le lien
    reset_url = f"{base_url}?action=reset&token={token}"

    # Envoyer l'email
    message = Mail(
        from_email=get_from_email(),
        to_emails=email,
        subject="🏠 Immo Maroc — Réinitialisation de votre mot de passe",
        html_content=f"""
        <div style="font-family: Georgia, serif; max-width: 600px; margin: 0 auto;
                    background: #1B4332; color: #FAF7F2; padding: 40px; border-radius: 16px;">

            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #D4AF37; font-size: 2rem; margin: 0;">🇲🇦 Immo Maroc</h1>
                <p style="color: rgba(250,247,242,0.7); letter-spacing: 2px; font-size: 0.85rem;">
                    VEILLE IMMOBILIÈRE MAROCAINE
                </p>
            </div>

            <div style="background: rgba(255,255,255,0.05); border-radius: 12px;
                        padding: 30px; border: 1px solid rgba(212,175,55,0.3);">
                <h2 style="color: #FAF7F2; margin-top: 0;">Réinitialisation du mot de passe</h2>
                <p style="color: rgba(250,247,242,0.8);">
                    Vous avez demandé à réinitialiser votre mot de passe.
                    Cliquez sur le bouton ci-dessous pour continuer.
                </p>
                <p style="color: rgba(250,247,242,0.6); font-size: 0.85rem;">
                    ⏰ Ce lien expire dans <b style="color: #D4AF37;">1 heure</b>.
                </p>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}"
                       style="background: linear-gradient(135deg, #D4AF37, #C1440E);
                              color: white; padding: 14px 32px; border-radius: 8px;
                              text-decoration: none; font-weight: 600; font-size: 1rem;
                              display: inline-block;">
                        🔑 Réinitialiser mon mot de passe
                    </a>
                </div>

                <p style="color: rgba(250,247,242,0.5); font-size: 0.8rem; text-align: center;">
                    Si vous n'avez pas demandé cette réinitialisation, ignorez cet email.
                </p>
            </div>

            <div style="text-align: center; margin-top: 20px; color: rgba(212,175,55,0.5);
                        font-size: 0.75rem;">
                ✦ ◆ ✦ ◆ ✦ ◆ ✦<br>
                Immo Maroc © 2026
            </div>
        </div>
        """
    )

    try:
        sg = SendGridAPIClient(get_sendgrid_key())
        sg.send(message)
        return True, "✅ Email envoyé ! Vérifiez votre boîte mail."
    except Exception as e:
        return False, f"❌ Erreur envoi email : {e}"


def verifier_token_reset(token):
    """Vérifie si un token est valide"""
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    ph = get_placeholder(db_type)

    cursor.execute(f"""
        SELECT email, expires_at, used FROM reset_tokens
        WHERE token = {ph}
    """, (token,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None, "❌ Lien invalide."

    email, expires_at, used = row

    if used:
        return None, "❌ Ce lien a déjà été utilisé."

    if datetime.now() > datetime.strptime(expires_at, "%Y-%m-%d %H:%M:%S"):
        return None, "❌ Ce lien a expiré."

    return email, "✅ Token valide"


def consommer_token_reset(token):
    """Marque le token comme utilisé"""
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    ph = get_placeholder(db_type)
    cursor.execute(f"UPDATE reset_tokens SET used = 1 WHERE token = {ph}", (token,))
    conn.commit()
    conn.close()


def envoyer_email_bienvenue(email, nom):
    """Email de bienvenue à l'inscription"""
    message = Mail(
        from_email=get_from_email(),
        to_emails=email,
        subject="🏠 Bienvenue sur Immo Maroc !",
        html_content=f"""
        <div style="font-family: Georgia, serif; max-width: 600px; margin: 0 auto;
                    background: #1B4332; color: #FAF7F2; padding: 40px; border-radius: 16px;">

            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #D4AF37; font-size: 2rem; margin: 0;">🇲🇦 Immo Maroc</h1>
            </div>

            <div style="background: rgba(255,255,255,0.05); border-radius: 12px;
                        padding: 30px; border: 1px solid rgba(212,175,55,0.3);">
                <h2 style="color: #FAF7F2;">Bienvenue {nom} ! 🎉</h2>
                <p style="color: rgba(250,247,242,0.8);">
                    Votre compte a été créé avec succès sur Immo Maroc.
                </p>

                <div style="background: rgba(212,175,55,0.1); border-radius: 8px;
                            padding: 20px; margin: 20px 0; border: 1px solid rgba(212,175,55,0.3);">
                    <h3 style="color: #D4AF37; margin-top: 0;">🎁 Votre cadeau de bienvenue</h3>
                    <p style="color: #FAF7F2; font-size: 1.2rem; margin: 0;">
                        <b>💎 5 crédits gratuits</b> pour commencer vos recherches !
                    </p>
                </div>

                <div style="text-align: center; margin: 20px 0;">
                    <a href="https://maghreb-immo.streamlit.app"
                       style="background: linear-gradient(135deg, #D4AF37, #C1440E);
                              color: white; padding: 14px 32px; border-radius: 8px;
                              text-decoration: none; font-weight: 600;">
                        🏠 Accéder à Immo Maroc
                    </a>
                </div>
            </div>

            <div style="text-align: center; margin-top: 20px; color: rgba(212,175,55,0.5);
                        font-size: 0.75rem;">
                ✦ ◆ ✦ ◆ ✦ ◆ ✦<br>Immo Maroc © 2026
            </div>
        </div>
        """
    )

    try:
        sg = SendGridAPIClient(get_sendgrid_key())
        sg.send(message)
        return True
    except:
        return False


if __name__ == "__main__":
    init_reset_table()
    print("✅ Service email initialisé")