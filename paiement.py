import stripe
import os
import sqlite3
from datetime import datetime

try:
    import streamlit as st
    stripe.api_key = st.secrets.get("STRIPE_SECRET_KEY", os.getenv("STRIPE_SECRET_KEY", ""))
except:
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

DB_PATH = "immo.db"


def init_users_db():
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


def creer_session_paiement(email, pack):
    packs = {
        "starter": {
            "nom": "Pack Starter — 100 crédits",
            "prix": 999,
            "credits": 100,
        },
        "pro": {
            "nom": "Pack Pro — 500 crédits",
            "prix": 3999,
            "credits": 500,
        },
        "business": {
            "nom": "Pack Business — 2000 crédits",
            "prix": 9999,
            "credits": 2000,
        }
    }

    if pack not in packs:
        return None

    p = packs[pack]

    try:
        # URL de base
        try:
            base_url = st.secrets.get("APP_URL", "http://localhost:8501")
        except:
            base_url = os.getenv("APP_URL", "http://localhost:8501")

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
            success_url=base_url + "?paiement=succes&email=" + email + "&pack=" + pack,
            cancel_url=base_url + "?paiement=annule",
            metadata={
                "email": email,
                "pack": pack,
                "credits": p["credits"]
            }
        )
        return session

    except Exception as e:
        print(f"❌ Erreur Stripe : {e}")
        return None


def ajouter_credits(email, credits, stripe_payment_id, montant_eur):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT OR IGNORE INTO utilisateurs (email, credits, date_inscription)
        VALUES (?, 0, ?)
    """, (email, now))

    cursor.execute("""
        UPDATE utilisateurs
        SET credits = credits + ?,
            date_derniere_recharge = ?
        WHERE email = ?
    """, (credits, now, email))

    cursor.execute("""
        INSERT INTO transactions (email, montant_eur, credits_ajoutes, stripe_payment_id, date_transaction, statut)
        VALUES (?, ?, ?, ?, ?, 'success')
    """, (email, montant_eur, credits, stripe_payment_id, now))

    conn.commit()
    conn.close()


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