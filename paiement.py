import stripe
import os
import sqlite3
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

DB_PATH = "immo.db"


def init_users_db():
    """Crée la table utilisateurs si elle n'existe pas"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS utilisateurs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            credits INTEGER DEFAULT 0,
            plan TEXT DEFAULT 'gratuit',
            stripe_customer_id TEXT,
            date_inscription TEXT,
            date_derniere_recharge TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            montant_eur REAL,
            credits_ajoutes INTEGER,
            stripe_payment_id TEXT,
            date_transaction TEXT,
            statut TEXT
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Tables utilisateurs et transactions créées")


def creer_session_paiement(email, pack):
    """Crée une session de paiement Stripe"""

    packs = {
        "starter": {
            "nom": "Pack Starter — 100 crédits",
            "prix": 999,  # en centimes = 9.99€
            "credits": 100,
        },
        "pro": {
            "nom": "Pack Pro — 500 crédits",
            "prix": 3999,  # 39.99€
            "credits": 500,
        },
        "business": {
            "nom": "Pack Business — 2000 crédits",
            "prix": 9999,  # 99.99€
            "credits": 2000,
        }
    }

    if pack not in packs:
        print(f"❌ Pack inconnu : {pack}")
        return None

    p = packs[pack]

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "eur",
                    "product_data": {
                        "name": p["nom"],
                        "description": f"Accès à {p['credits']} recherches immobilières sur Immo Maroc"
                    },
                    "unit_amount": p["prix"],
                },
                "quantity": 1,
            }],
            mode="payment",
            customer_email=email,
            success_url="http://localhost:8501?paiement=succes&email=" + email + "&pack=" + pack,
            cancel_url="http://localhost:8501?paiement=annule",
            metadata={
                "email": email,
                "pack": pack,
                "credits": p["credits"]
            }
        )

        print(f"✅ Session créée pour {email} — Pack {pack}")
        print(f"   🔗 URL de paiement : {session.url}")
        return session

    except Exception as e:
        print(f"❌ Erreur Stripe : {e}")
        return None


def ajouter_credits(email, credits, stripe_payment_id, montant_eur):
    """Ajoute des crédits à un utilisateur après paiement"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Créer l'utilisateur s'il n'existe pas
    cursor.execute("""
        INSERT OR IGNORE INTO utilisateurs (email, credits, date_inscription)
        VALUES (?, 0, ?)
    """, (email, now))

    # Ajouter les crédits
    cursor.execute("""
        UPDATE utilisateurs
        SET credits = credits + ?,
            date_derniere_recharge = ?
        WHERE email = ?
    """, (credits, now, email))

    # Enregistrer la transaction
    cursor.execute("""
        INSERT INTO transactions (email, montant_eur, credits_ajoutes, stripe_payment_id, date_transaction, statut)
        VALUES (?, ?, ?, ?, ?, 'success')
    """, (email, montant_eur, credits, stripe_payment_id, now))

    conn.commit()
    conn.close()
    print(f"✅ {credits} crédits ajoutés pour {email}")


def get_credits(email):
    """Retourne le nombre de crédits d'un utilisateur"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT credits FROM utilisateurs WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0


def utiliser_credit(email):
    """Utilise 1 crédit — retourne True si OK, False si pas assez de crédits"""
    credits = get_credits(email)
    if credits <= 0:
        return False

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE utilisateurs SET credits = credits - 1 WHERE email = ?
    """, (email,))
    conn.commit()
    conn.close()
    return True


if __name__ == "__main__":
    # Test
    init_users_db()

    print("\n🧪 Test création session Stripe...")
    session = creer_session_paiement("test@immomaroc.ma", "starter")

    if session:
        print(f"\n✅ Tout fonctionne !")
        print(f"   Ouvre cette URL pour tester le paiement :")
        print(f"   {session.url}")