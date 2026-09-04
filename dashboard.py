import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import folium
import uuid
import random
import os
from streamlit_folium import st_folium

# ── Charger les secrets (Streamlit Cloud ou local)
try:
    for key in ["GROQ_API_KEY", "STRIPE_PUBLIC_KEY", "STRIPE_SECRET_KEY", "DATABASE_URL"]:
        if key not in os.environ:
            val = st.secrets.get(key, "")
            if val:
                os.environ[key] = val
except:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except:
        pass

from db_config import get_db_connection, get_placeholder
from auth import (init_auth_db, inscrire_utilisateur, connecter_utilisateur,
                  get_credits, utiliser_credit, ajouter_credits,
                  get_session_anonyme, utiliser_recherche_anonyme, enregistrer_recherche)
from paiement import creer_session_paiement

VILLES_COORDS = {
    'Casablanca': [33.5731, -7.5898],
    'Rabat': [34.0209, -6.8416],
    'Marrakech': [31.6295, -7.9811],
    'Fès': [34.0181, -5.0078],
    'Tanger': [35.7595, -5.8340],
    'Agadir': [30.4278, -9.5981],
    'Meknès': [33.8935, -5.5473],
    'Oujda': [34.6814, -1.9086],
    'Kénitra': [34.2610, -6.5802],
    'Tétouan': [35.5785, -5.3684],
    'Salé': [34.0531, -6.7985],
    'Nador': [35.1681, -2.9287],
    'Mohammedia': [33.6866, -7.3830],
    'El Jadida': [33.2316, -8.5007],
    'Béni Mellal': [32.3373, -6.3498],
    'Settat': [33.0010, -7.6197],
    'Temara': [33.9287, -6.9091],
    'Bouznika': [33.7914, -7.1586],
    'Guéliz': [31.6340, -8.0089],
    'Ain Sebaa': [33.6070, -7.5150],
    'Bouskoura': [33.4500, -7.6500],
    'Dar Bouazza': [33.4833, -7.7667],
}

PUBS = [
    {
        "titre": "🏠 Mubawab.ma",
        "desc": "Plus de 100 000 annonces immobilières au Maroc. Trouvez votre bien idéal !",
        "texte_banniere": "🏠 Mubawab.ma — Des milliers d'annonces au Maroc",
        "url": "https://www.mubawab.ma",
        "cta": "Voir les annonces",
        "cta_court": "Voir →"
    },
    {
        "titre": "🔑 Yakeey.ma",
        "desc": "L'immobilier neuf au Maroc — programmes, résidences, investissements.",
        "texte_banniere": "🔑 Yakeey.ma — L'immobilier neuf au Maroc",
        "url": "https://www.yakeey.com",
        "cta": "Découvrir Yakeey",
        "cta_court": "Découvrir →"
    },
    {
        "titre": "🏡 Sarouty.ma",
        "desc": "Achat, vente, location — toute l'immobilier marocain en un clic.",
        "texte_banniere": "🏡 Sarouty.ma — Achat, vente, location au Maroc",
        "url": "https://www.sarouty.ma",
        "cta": "Explorer Sarouty",
        "cta_court": "Explorer →"
    },
]

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap');

html, body, [class*="css"], .stApp, .main, .block-container {
    background-color: #1B4332 !important;
    font-family: 'Inter', sans-serif;
    color: #FAF7F2 !important;
}
.main-header {
    background: linear-gradient(135deg, #0a1f17 0%, #1B4332 40%, #D4AF37 100%);
    padding: 40px 30px;
    border-radius: 16px;
    margin-bottom: 30px;
    position: relative;
    overflow: hidden;
    border: 1px solid rgba(212, 175, 55, 0.3);
}
.main-header::before {
    content: "✦ ◆ ✦ ◆ ✦ ◆ ✦ ◆ ✦ ◆ ✦ ◆ ✦";
    position: absolute;
    top: 8px; left: 0; right: 0;
    text-align: center;
    color: rgba(212, 175, 55, 0.5);
    font-size: 11px;
    letter-spacing: 8px;
}
.main-header::after {
    content: "✦ ◆ ✦ ◆ ✦ ◆ ✦ ◆ ✦ ◆ ✦ ◆ ✦";
    position: absolute;
    bottom: 8px; left: 0; right: 0;
    text-align: center;
    color: rgba(212, 175, 55, 0.5);
    font-size: 11px;
    letter-spacing: 8px;
}
.main-title {
    font-family: 'Playfair Display', serif;
    font-size: 2.8rem;
    font-weight: 700;
    color: #FAF7F2;
    text-align: center;
    margin: 0;
    text-shadow: 2px 2px 8px rgba(0,0,0,0.4);
}
.main-subtitle {
    font-size: 0.95rem;
    color: #D4AF37;
    text-align: center;
    margin-top: 8px;
    letter-spacing: 3px;
    text-transform: uppercase;
}
.kpi-card {
    background: rgba(255,255,255,0.07);
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    border: 1px solid rgba(212, 175, 55, 0.4);
    border-top: 4px solid #D4AF37;
    margin-bottom: 10px;
}
.kpi-value {
    font-family: 'Playfair Display', serif;
    font-size: 2rem;
    font-weight: 700;
    color: #D4AF37;
}
.kpi-label {
    font-size: 0.82rem;
    color: rgba(250, 247, 242, 0.7);
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 4px;
}
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a1f17 0%, #112b21 100%) !important;
    border-right: 2px solid #D4AF37 !important;
}
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] div,
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #FAF7F2 !important;
}
section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
    background-color: #0a1f17 !important;
    border: 1px solid rgba(212, 175, 55, 0.4) !important;
    border-radius: 8px !important;
}
section[data-testid="stSidebar"] div[data-baseweb="select"] *,
section[data-testid="stSidebar"] div[data-baseweb="select"] div,
section[data-testid="stSidebar"] div[data-baseweb="select"] span,
section[data-testid="stSidebar"] div[data-baseweb="select"] input {
    color: #FAF7F2 !important;
    background-color: transparent !important;
    -webkit-text-fill-color: #FAF7F2 !important;
}
section[data-testid="stSidebar"] div[data-baseweb="select"] svg {
    fill: #D4AF37 !important;
}
section[data-testid="stSidebar"] input[type="number"],
section[data-testid="stSidebar"] input[type="text"],
section[data-testid="stSidebar"] input[type="email"],
section[data-testid="stSidebar"] input[type="password"] {
    background-color: #0a1f17 !important;
    color: #FAF7F2 !important;
    -webkit-text-fill-color: #FAF7F2 !important;
    border: 1px solid rgba(212, 175, 55, 0.4) !important;
    border-radius: 8px !important;
}
section[data-testid="stSidebar"] .stNumberInput > div {
    background-color: #0a1f17 !important;
    border: 1px solid rgba(212, 175, 55, 0.4) !important;
    border-radius: 8px !important;
}
section[data-testid="stSidebar"] .stNumberInput button {
    background-color: #1B4332 !important;
    color: #D4AF37 !important;
    border: none !important;
}
.sidebar-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.3rem;
    color: #D4AF37 !important;
    text-align: center;
    padding: 10px 0;
    border-bottom: 1px solid rgba(212, 175, 55, 0.3);
    margin-bottom: 15px;
}
div[data-baseweb="popover"],
div[data-baseweb="popover"] * {
    background-color: #0a1f17 !important;
    color: #FAF7F2 !important;
}
div[data-baseweb="menu"] {
    background-color: #0a1f17 !important;
    border: 1px solid rgba(212, 175, 55, 0.4) !important;
    border-radius: 8px !important;
}
div[role="option"] {
    background-color: #0a1f17 !important;
    color: #FAF7F2 !important;
}
div[role="option"]:hover {
    background-color: rgba(212, 175, 55, 0.15) !important;
    color: #D4AF37 !important;
}
div[aria-selected="true"] {
    background-color: rgba(212, 175, 55, 0.2) !important;
    color: #D4AF37 !important;
    font-weight: 600 !important;
}
.stTabs [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.06);
    border-radius: 10px;
    padding: 4px;
    border: 1px solid rgba(212, 175, 55, 0.2);
}
.stTabs [data-baseweb="tab"] {
    color: rgba(250, 247, 242, 0.7) !important;
    border-radius: 8px;
    padding: 8px 20px;
    font-weight: 500;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #D4AF37, #C1440E) !important;
    color: white !important;
}
.annonce-card {
    background: rgba(255,255,255,0.06);
    border-radius: 12px;
    padding: 16px 20px;
    margin: 8px 0;
    border: 1px solid rgba(212, 175, 55, 0.2);
    border-left: 4px solid #D4AF37;
    transition: transform 0.2s, background 0.2s;
}
.annonce-card:hover {
    transform: translateX(4px);
    background: rgba(255,255,255,0.1);
}
.annonce-titre {
    font-family: 'Playfair Display', serif;
    font-size: 1rem;
    font-weight: 600;
    color: #FAF7F2;
    margin-bottom: 10px;
}
.annonce-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 500;
    margin-right: 6px;
    margin-top: 4px;
}
.badge-prix { background: rgba(212,175,55,0.15); color: #D4AF37; border: 1px solid rgba(212,175,55,0.5); }
.badge-surface { background: rgba(99,179,237,0.15); color: #90CDF4; border: 1px solid rgba(99,179,237,0.4); }
.badge-ville { background: rgba(154,230,180,0.15); color: #9AE6B4; border: 1px solid rgba(154,230,180,0.4); }
.badge-source { background: rgba(252,129,74,0.15); color: #FC814A; border: 1px solid rgba(252,129,74,0.4); }
.alerte-card {
    background: rgba(212, 175, 55, 0.08);
    border-radius: 10px;
    padding: 14px 18px;
    margin: 8px 0;
    border: 1px solid rgba(212, 175, 55, 0.3);
    border-left: 4px solid #D4AF37;
}
.section-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.3rem;
    color: #D4AF37;
    border-bottom: 1px solid rgba(212, 175, 55, 0.3);
    padding-bottom: 8px;
    margin-bottom: 16px;
}
.separateur {
    text-align: center;
    color: #D4AF37;
    font-size: 1.2rem;
    letter-spacing: 12px;
    margin: 20px 0;
    opacity: 0.5;
}
.credits-badge {
    background: linear-gradient(135deg, #D4AF37, #C1440E);
    color: white !important;
    padding: 6px 16px;
    border-radius: 20px;
    font-weight: 600;
    font-size: 0.9rem;
    display: inline-block;
    margin: 5px 0;
}
.pub-card {
    background: rgba(212, 175, 55, 0.06);
    border: 1px dashed rgba(212, 175, 55, 0.4);
    border-radius: 10px;
    padding: 14px;
    text-align: center;
    margin: 10px 0;
}
.lock-card {
    background: rgba(193, 68, 14, 0.1);
    border: 1px solid rgba(193, 68, 14, 0.4);
    border-radius: 12px;
    padding: 24px;
    text-align: center;
    margin: 20px 0;
}
.stButton button {
    background: linear-gradient(135deg, #D4AF37, #C1440E) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    width: 100% !important;
}
.modal-overlay {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0,0,0,0.75);
    z-index: 9999;
    display: flex;
    align-items: center;
    justify-content: center;
    backdrop-filter: blur(4px);
}
.modal-content {
    background: linear-gradient(135deg, #0a1f17, #1B4332);
    border: 1px solid #D4AF37;
    border-radius: 16px;
    padding: 32px;
    max-width: 460px;
    width: 90%;
    text-align: center;
    position: relative;
    box-shadow: 0 20px 60px rgba(0,0,0,0.6);
    animation: fadeInScale 0.3s ease;
}
@keyframes fadeInScale {
    from { opacity: 0; transform: scale(0.9); }
    to { opacity: 1; transform: scale(1); }
}
.banniere-bas {
    position: fixed;
    bottom: 0; left: 0; right: 0;
    background: linear-gradient(90deg, #0a1f17 0%, #1B4332 50%, #0a1f17 100%);
    border-top: 1px solid rgba(212,175,55,0.4);
    padding: 10px 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    z-index: 1000;
    gap: 12px;
}
.succes-paiement {
    background: linear-gradient(135deg, rgba(82,183,136,0.2), rgba(27,67,50,0.8));
    border: 1px solid #52B788;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    margin-bottom: 20px;
}
p, span, label, h1, h2, h3 {
    color: #FAF7F2 !important;
}
</style>
"""


def get_annonces(ville=None, prix_min=None, prix_max=None, surface_min=None, surface_max=None, source=None):
    try:
        conn, db_type = get_db_connection()
        ph = get_placeholder(db_type)
        query = "SELECT * FROM annonces WHERE 1=1"
        params = []
        if ville and ville != "Toutes":
            query += f" AND ville = {ph}"
            params.append(ville)
        if prix_min:
            query += f" AND prix_dh >= {ph}"
            params.append(prix_min)
        if prix_max:
            query += f" AND prix_dh <= {ph}"
            params.append(prix_max)
        if surface_min:
            query += f" AND surface_m2 >= {ph}"
            params.append(surface_min)
        if surface_max:
            query += f" AND surface_m2 <= {ph}"
            params.append(surface_max)
        if source and source != "Toutes":
            query += f" AND source = {ph}"
            params.append(source)
        query += " ORDER BY prix_dh ASC"
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df
    except Exception as e:
        print(f"Erreur get_annonces: {e}")
        return pd.DataFrame()


def get_villes():
    try:
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT ville FROM annonces WHERE ville IS NOT NULL ORDER BY ville")
        villes = ["Toutes"] + [row[0] for row in cursor.fetchall()]
        conn.close()
        return villes
    except:
        return ["Toutes"]


def get_sources():
    try:
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT source FROM annonces ORDER BY source")
        sources = ["Toutes"] + [row[0] for row in cursor.fetchall()]
        conn.close()
        return sources
    except:
        return ["Toutes"]


def get_stats():
    try:
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM annonces")
        total = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM annonces WHERE prix_dh IS NOT NULL")
        avec_prix = cursor.fetchone()[0]
        cursor.execute("SELECT AVG(prix_dh) FROM annonces WHERE prix_dh IS NOT NULL")
        prix_moyen = cursor.fetchone()[0]
        cursor.execute("SELECT AVG(prix_m2) FROM annonces WHERE prix_m2 IS NOT NULL")
        prix_m2_moyen = cursor.fetchone()[0]
        conn.close()
        return total, avec_prix, prix_moyen, prix_m2_moyen
    except:
        return 0, 0, None, None


def get_alertes(budget_max, surface_min, ville=None):
    try:
        conn, db_type = get_db_connection()
        ph = get_placeholder(db_type)
        query = f"""
            SELECT titre, prix_dh, surface_m2, prix_m2, ville, url, source
            FROM annonces
            WHERE prix_dh <= {ph} AND prix_dh IS NOT NULL
            AND surface_m2 >= {ph} AND surface_m2 IS NOT NULL
        """
        params = [budget_max, surface_min]
        if ville and ville != "Toutes":
            query += f" AND ville = {ph}"
            params.append(ville)
        query += " ORDER BY prix_dh ASC LIMIT 10"
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df
    except:
        return pd.DataFrame()


def afficher_pub_sidebar():
    pub = random.choice(PUBS)
    st.sidebar.markdown(f"""
    <div style="background:rgba(212,175,55,0.06); border:1px dashed rgba(212,175,55,0.4);
         border-radius:10px; padding:12px; text-align:center; margin:8px 0;">
        <div style="font-size:0.65rem; color:rgba(250,247,242,0.4);
             text-transform:uppercase; letter-spacing:2px; margin-bottom:6px;">Publicité</div>
        <b style="color:#D4AF37; font-size:0.9rem;">{pub['titre']}</b><br>
        <span style="font-size:0.75rem; color:rgba(250,247,242,0.6);">{pub['desc'][:60]}...</span><br>
        <a href="{pub['url']}" target="_blank"
           style="color:#D4AF37; font-weight:600; text-decoration:none; font-size:0.8rem;">
            {pub['cta_court']}
        </a>
    </div>
    """, unsafe_allow_html=True)


def afficher_sidebar_auth():
    st.sidebar.markdown('<div class="sidebar-title">✦ Filtres ✦</div>', unsafe_allow_html=True)

    if st.session_state.get("user_email"):
        email = st.session_state["user_email"]
        credits = get_credits(email)
        st.sidebar.markdown(f"""
        <div style="text-align:center; margin-bottom:10px; padding:10px;
             background:rgba(212,175,55,0.08); border-radius:8px;
             border:1px solid rgba(212,175,55,0.3);">
            <div style="color:#9AE6B4; font-size:0.85rem;">✅ Connecté</div>
            <div style="color:#D4AF37; font-size:0.8rem;">{email}</div>
            <div class="credits-badge">💎 {credits} crédits</div>
        </div>
        """, unsafe_allow_html=True)
        if st.sidebar.button("🚪 Déconnexion"):
            st.session_state.pop("user_email", None)
            st.session_state.pop("resultats_recherche", None)
            st.session_state["modal_shown"] = False
            st.rerun()
    else:
        if "session_id" not in st.session_state:
            st.session_state["session_id"] = str(uuid.uuid4())
        session = get_session_anonyme(st.session_state["session_id"])
        restantes = session[1] if session else 5
        st.sidebar.markdown(f"""
        <div style="text-align:center; margin-bottom:10px; padding:10px;
             background:rgba(212,175,55,0.08); border-radius:8px;
             border:1px solid rgba(212,175,55,0.3);">
            <div style="color:#D4AF37; font-weight:600;">👤 Visiteur anonyme</div>
            <div style="color:#FAF7F2; font-size:0.85rem; margin-top:4px;">
                🔍 {restantes} recherche(s) gratuite(s)
            </div>
        </div>
        """, unsafe_allow_html=True)

        with st.sidebar.expander("🔐 Se connecter / S'inscrire"):
            mode = st.radio("Mode", ["Connexion", "Inscription"], horizontal=True, label_visibility="collapsed")
            if mode == "Connexion":
                email = st.text_input("📧 Email", key="login_email")
                password = st.text_input("🔒 Mot de passe", type="password", key="login_password")
                if st.button("Se connecter"):
                    user = connecter_utilisateur(email, password)
                    if user:
                        st.session_state["user_email"] = email
                        st.session_state.pop("resultats_recherche", None)
                        st.session_state["modal_shown"] = False
                        st.success("✅ Connecté !")
                        st.rerun()
                    else:
                        st.error("❌ Email ou mot de passe incorrect")
            else:
                nom = st.text_input("👤 Nom", key="reg_nom")
                email = st.text_input("📧 Email", key="reg_email")
                password = st.text_input("🔒 Mot de passe", type="password", key="reg_password")
                if st.button("S'inscrire"):
                    ok, msg = inscrire_utilisateur(email, password, nom)
                    if ok:
                        st.session_state["user_email"] = email
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

    st.sidebar.markdown("---")


# ════════════════════════════════
# INIT
# ════════════════════════════════
init_auth_db()

st.set_page_config(
    page_title="Immo Maroc — Veille Immobilière",
    page_icon="https://flagcdn.com/w20/ma.png",
    layout="wide"
)
st.markdown(CSS, unsafe_allow_html=True)

# ── Retour paiement Stripe
query_params = st.query_params
paiement_status = query_params.get("paiement", "")
email_paye = query_params.get("email", "")
pack_paye = query_params.get("pack", "")
credits_map = {"starter": 100, "pro": 500, "business": 2000}

if paiement_status == "succes" and email_paye and pack_paye:
    credits_a_ajouter = credits_map.get(pack_paye, 0)
    cle = f"paiement_traite_{pack_paye}_{email_paye}"
    if credits_a_ajouter > 0 and not st.session_state.get(cle):
        ajouter_credits(email_paye, credits_a_ajouter)
        st.session_state[cle] = True
        st.session_state["user_email"] = email_paye
        st.session_state["paiement_succes"] = {"pack": pack_paye, "credits": credits_a_ajouter}
    st.query_params.clear()

est_payant = False
if st.session_state.get("user_email"):
    est_payant = get_credits(st.session_state["user_email"]) > 50

# ── Modal pub
if "modal_shown" not in st.session_state:
    st.session_state["modal_shown"] = False

if not st.session_state["modal_shown"] and not est_payant:
    pub = random.choice(PUBS)
    st.markdown(f"""
    <div class="modal-overlay" id="modal-pub">
        <div class="modal-content">
            <div style="font-size:0.7rem; color:rgba(250,247,242,0.4);
                 text-transform:uppercase; letter-spacing:2px; margin-bottom:12px;">
                Publicité partenaire — Soutenez Immo Maroc
            </div>
            <div style="font-size:2.5rem; margin-bottom:8px;">🏠</div>
            <div style="font-family:'Playfair Display',serif; font-size:1.4rem;
                 color:#D4AF37; margin-bottom:12px; font-weight:700;">{pub['titre']}</div>
            <div style="color:rgba(250,247,242,0.8); font-size:0.9rem;
                 margin-bottom:24px; line-height:1.6;">{pub['desc']}</div>
            <div style="display:flex; gap:10px; justify-content:center; flex-wrap:wrap;">
                <a href="{pub['url']}" target="_blank"
                   style="background:linear-gradient(135deg,#D4AF37,#C1440E);
                          color:white; padding:10px 24px; border-radius:8px;
                          font-weight:600; text-decoration:none; font-size:0.9rem;">
                    {pub['cta']} →
                </a>
                <button onclick="document.getElementById('modal-pub').style.display='none'"
                        style="background:rgba(255,255,255,0.08); color:#FAF7F2;
                               padding:10px 24px; border-radius:8px;
                               border:1px solid rgba(255,255,255,0.2);
                               font-weight:600; cursor:pointer; font-size:0.9rem;">
                    ✕ Fermer
                </button>
            </div>
            <div style="margin-top:16px; font-size:0.72rem; color:rgba(250,247,242,0.3);">
                Supprimez les pubs en passant à un pack payant
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.session_state["modal_shown"] = True

# ── Header
st.markdown("""
<div class="main-header">
    <div class="main-title">
        <img src="https://flagcdn.com/w40/ma.png"
             style="height:45px; vertical-align:middle; margin-right:12px;
                    border-radius:4px; box-shadow:0 2px 8px rgba(0,0,0,0.3);">
        Immo Maroc
    </div>
    <div class="main-subtitle">Veille intelligente du marché immobilier marocain</div>
</div>
""", unsafe_allow_html=True)

# ── Notification paiement
if st.session_state.get("paiement_succes"):
    info = st.session_state["paiement_succes"]
    st.markdown(f"""
    <div class="succes-paiement">
        <div style="font-size:2rem;">🎉</div>
        <div style="font-family:'Playfair Display',serif; font-size:1.3rem; color:#52B788; margin:8px 0;">
            Paiement confirmé !</div>
        <div style="color:#FAF7F2; font-size:0.95rem;">
            Pack <b style="color:#D4AF37;">{info['pack'].capitalize()}</b> activé —
            <b style="color:#D4AF37;">+{info['credits']} crédits</b> ajoutés
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.session_state.pop("paiement_succes", None)

# ── Sidebar
afficher_sidebar_auth()
villes = get_villes()
ville_choisie = st.sidebar.selectbox("🏙️ Ville", villes)
sources = get_sources()
source_choisie = st.sidebar.selectbox("🌐 Source", sources)
st.sidebar.markdown("---")
st.sidebar.markdown("**💰 Budget (DH)**")
prix_min = st.sidebar.number_input("Minimum", min_value=0, value=0, step=50000)
prix_max = st.sidebar.number_input("Maximum", min_value=0, value=10000000, step=50000)
st.sidebar.markdown("**📐 Surface (m²)**")
surface_min = st.sidebar.number_input("Minimum ", min_value=0, value=0, step=10)
surface_max = st.sidebar.number_input("Maximum ", min_value=0, value=1000, step=10)
st.sidebar.markdown("---")

if not est_payant:
    afficher_pub_sidebar()

st.sidebar.markdown("""
<div style="text-align:center; color:#D4AF37; font-size:0.8rem; opacity:0.7; margin-top:10px;">
✦ ◆ ✦ ◆ ✦ ◆ ✦<br>Immo Maroc © 2026
</div>
""", unsafe_allow_html=True)

# ── Données
df = get_annonces(
    ville=ville_choisie,
    prix_min=prix_min if prix_min > 0 else None,
    prix_max=prix_max if prix_max < 10000000 else None,
    surface_min=surface_min if surface_min > 0 else None,
    surface_max=surface_max if surface_max < 1000 else None,
    source=source_choisie
)
total, avec_prix, prix_moyen, prix_m2_moyen = get_stats()

# ── Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Tableau de bord", "🗺️ Carte interactive", "🔔 Alertes & Recherche", "💳 Recharger"])

# ════════════════════════════════
# TAB 1
# ════════════════════════════════
with tab1:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="kpi-card"><div class="kpi-value">{total}</div><div class="kpi-label">📦 Total annonces</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="kpi-card"><div class="kpi-value">{avec_prix}</div><div class="kpi-label">💰 Avec prix</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="kpi-card"><div class="kpi-value">{f"{int(prix_moyen):,}" if prix_moyen else "N/A"}</div><div class="kpi-label">📊 Prix moyen DH</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="kpi-card"><div class="kpi-value">{f"{int(prix_m2_moyen):,}" if prix_m2_moyen else "N/A"}</div><div class="kpi-label">📐 Prix/m² moyen</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="separateur">✦ ◆ ✦ ◆ ✦</div>', unsafe_allow_html=True)

    if df.empty:
        st.info("📭 Aucune annonce disponible pour le moment.")
    else:
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown('<div class="section-title">📍 Annonces par ville</div>', unsafe_allow_html=True)
            df_villes = df[df['ville'].notna()]
            if not df_villes.empty:
                fig = px.bar(
                    df_villes.groupby('ville').size().reset_index(name='count').sort_values('count', ascending=False).head(10),
                    x='ville', y='count', color='count',
                    color_continuous_scale=[[0, '#2d6a4f'], [0.5, '#D4AF37'], [1, '#C1440E']],
                    labels={'ville': 'Ville', 'count': 'Annonces'}
                )
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#FAF7F2', family='Inter'), coloraxis_showscale=False)
                fig.update_xaxes(tickcolor='#FAF7F2', gridcolor='rgba(255,255,255,0.1)')
                fig.update_yaxes(tickcolor='#FAF7F2', gridcolor='rgba(255,255,255,0.1)')
                st.plotly_chart(fig, use_container_width=True)

        with col_g2:
            st.markdown('<div class="section-title">💰 Distribution des prix</div>', unsafe_allow_html=True)
            df_prix = df[df['prix_dh'].notna()]
            if not df_prix.empty:
                fig = px.histogram(df_prix, x='prix_dh', nbins=20,
                    color_discrete_sequence=['#D4AF37'], labels={'prix_dh': 'Prix (DH)'})
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#FAF7F2', family='Inter'))
                fig.update_xaxes(tickcolor='#FAF7F2', gridcolor='rgba(255,255,255,0.1)')
                fig.update_yaxes(tickcolor='#FAF7F2', gridcolor='rgba(255,255,255,0.1)')
                st.plotly_chart(fig, use_container_width=True)

        st.markdown('<div class="section-title">📊 Prix vs Surface</div>', unsafe_allow_html=True)
        df_scatter = df[df['prix_dh'].notna() & df['surface_m2'].notna()]
        if not df_scatter.empty:
            fig = px.scatter(df_scatter, x='surface_m2', y='prix_dh', color='ville',
                hover_data=['titre', 'type_bien'],
                color_discrete_sequence=['#D4AF37', '#C1440E', '#52B788', '#90CDF4', '#FC814A', '#B794F4'],
                labels={'surface_m2': 'Surface (m²)', 'prix_dh': 'Prix (DH)'})
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#FAF7F2', family='Inter'),
                legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(color='#FAF7F2')))
            fig.update_xaxes(tickcolor='#FAF7F2', gridcolor='rgba(255,255,255,0.1)')
            fig.update_yaxes(tickcolor='#FAF7F2', gridcolor='rgba(255,255,255,0.1)')
            st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="separateur">✦ ◆ ✦ ◆ ✦</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-title">📋 Annonces ({len(df)} résultats)</div>', unsafe_allow_html=True)

    if not df.empty:
        for i, (_, row) in enumerate(df.iterrows()):
            if i >= 5 and not st.session_state.get("user_email"):
                st.markdown("""
                <div class="lock-card">
                    <div style="font-size:2rem;">🔒</div>
                    <div style="font-family:'Playfair Display',serif; font-size:1.2rem; color:#D4AF37; margin:8px 0;">
                        Inscrivez-vous gratuitement</div>
                    <div style="color:rgba(250,247,242,0.7); font-size:0.9rem;">
                        Créez un compte gratuit pour voir toutes les annonces</div>
                </div>
                """, unsafe_allow_html=True)
                break
            prix_str = f"{int(row['prix_dh']):,} DH" if pd.notna(row['prix_dh']) else "Prix non spécifié"
            surface_str = f"{int(row['surface_m2'])} m²" if pd.notna(row['surface_m2']) else "Surface N/A"
            ville_str = row['ville'] if pd.notna(row['ville']) else "N/A"
            source_str = row['source'] if pd.notna(row['source']) else ""
            lien = row['url'] if pd.notna(row['url']) and row['url'] else "#"
            titre = row['titre'] if pd.notna(row['titre']) else "Appartement à vendre"
            st.markdown(f"""
            <div class="annonce-card">
                <div class="annonce-titre">🏠 {titre[:70]}</div>
                <span class="annonce-badge badge-prix">💰 {prix_str}</span>
                <span class="annonce-badge badge-surface">📐 {surface_str}</span>
                <span class="annonce-badge badge-ville">🏙️ {ville_str}</span>
                <span class="annonce-badge badge-source">🌐 {source_str}</span>
                <a href="{lien}" target="_blank"
                   style="float:right; color:#D4AF37; font-weight:600; text-decoration:none; font-size:0.85rem;">
                    Voir l'annonce →
                </a>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("📭 Aucune annonce disponible.")

# ════════════════════════════════
# TAB 2
# ════════════════════════════════
with tab2:
    st.markdown('<div class="section-title">🗺️ Carte des annonces par ville</div>', unsafe_allow_html=True)
    carte = folium.Map(location=[31.7917, -7.0926], zoom_start=6, tiles='CartoDB dark_matter')
    if not df.empty:
        df_carte = df[df['ville'].notna() & df['prix_dh'].notna()]
        if not df_carte.empty:
            stats_villes = df_carte.groupby('ville').agg(
                nb_annonces=('prix_dh', 'count'),
                prix_moyen=('prix_dh', 'mean'),
                prix_m2_moyen=('prix_m2', 'mean')
            ).reset_index()
            for _, row in stats_villes.iterrows():
                ville = row['ville']
                if ville in VILLES_COORDS:
                    coords = VILLES_COORDS[ville]
                    nb = int(row['nb_annonces'])
                    prix_moy = int(row['prix_moyen'])
                    prix_m2 = int(row['prix_m2_moyen']) if pd.notna(row['prix_m2_moyen']) else 0
                    rayon = max(12, nb * 5)
                    popup_html = f"""
                    <div style="font-family:Georgia; min-width:200px; padding:10px;
                         background:#1B4332; color:#FAF7F2; border-radius:8px; border:1px solid #D4AF37;">
                        <h4 style="color:#D4AF37; margin:0 0 8px 0;
                            border-bottom:1px solid rgba(212,175,55,0.4); padding-bottom:6px;">
                            🕌 {ville}</h4>
                        <b>📦 Annonces :</b> {nb}<br>
                        <b>💰 Prix moyen :</b> {prix_moy:,} DH<br>
                        <b>📐 Prix/m² :</b> {prix_m2:,} DH/m²
                    </div>
                    """
                    folium.CircleMarker(
                        location=coords, radius=rayon,
                        color='#D4AF37', fill=True,
                        fill_color='#52B788', fill_opacity=0.7,
                        popup=folium.Popup(popup_html, max_width=250),
                        tooltip=f"🕌 {ville} — {nb} annonces — {prix_moy:,} DH"
                    ).add_to(carte)
    st_folium(carte, width=None, height=520)
    st.caption("💡 Cliquez sur un cercle pour voir les détails.")

# ════════════════════════════════
# TAB 3
# ════════════════════════════════
with tab3:
    st.markdown('<div class="section-title">🔔 Recherche personnalisée</div>', unsafe_allow_html=True)

    if st.session_state.get("user_email"):
        credits = get_credits(st.session_state["user_email"])
        st.markdown(f'<div style="margin-bottom:10px;"><span class="credits-badge">💎 {credits} crédits disponibles</span></div>', unsafe_allow_html=True)
        peut_chercher = credits > 0
    else:
        if "session_id" not in st.session_state:
            st.session_state["session_id"] = str(uuid.uuid4())
        session = get_session_anonyme(st.session_state["session_id"])
        restantes = session[1] if session else 0
        st.info(f"👤 Visiteur anonyme — {restantes} recherche(s) gratuite(s) restante(s)")
        peut_chercher = restantes > 0

    col_a1, col_a2, col_a3 = st.columns(3)
    with col_a1:
        budget_alerte = st.number_input("💰 Budget maximum (DH)", min_value=100000, max_value=20000000, value=1000000, step=50000)
    with col_a2:
        surface_alerte = st.number_input("📐 Surface minimum (m²)", min_value=20, max_value=500, value=60, step=10)
    with col_a3:
        ville_alerte = st.selectbox("🏙️ Ville", get_villes(), key="ville_alerte")

    if peut_chercher:
        if st.button("🔍 Lancer la recherche (1 crédit)", type="primary"):
            credit_ok = False
            if st.session_state.get("user_email"):
                credit_ok = utiliser_credit(st.session_state["user_email"])
            else:
                credit_ok = utiliser_recherche_anonyme(st.session_state["session_id"])

            if not credit_ok:
                st.error("❌ Plus de crédits disponibles !")
                st.session_state.pop("resultats_recherche", None)
            else:
                enregistrer_recherche(
                    email=st.session_state.get("user_email"),
                    session_id=st.session_state.get("session_id"),
                    ville=ville_alerte,
                    budget_max=budget_alerte,
                    surface_min=surface_alerte
                )
                df_res = get_alertes(budget_alerte, surface_alerte, ville_alerte)
                st.session_state["resultats_recherche"] = df_res.to_dict('records') if not df_res.empty else []
                st.rerun()
    else:
        st.markdown("""
        <div class="lock-card">
            <div style="font-size:2rem;">🔒</div>
            <div style="font-family:'Playfair Display',serif; font-size:1.2rem; color:#D4AF37; margin:8px 0;">
                Plus de recherches disponibles</div>
            <div style="color:rgba(250,247,242,0.7); font-size:0.9rem;">
                Inscrivez-vous gratuitement ou rechargez vos crédits</div>
        </div>
        """, unsafe_allow_html=True)

    if "resultats_recherche" in st.session_state:
        resultats = st.session_state["resultats_recherche"]
        if resultats:
            st.success(f"✅ {len(resultats)} annonce(s) trouvée(s) !")
            for row in resultats:
                col1, col2 = st.columns([4, 1])
                with col1:
                    prix_str = f"{int(row['prix_dh']):,} DH" if row.get('prix_dh') else "N/A"
                    surface_str = f"{int(row['surface_m2'])} m²" if row.get('surface_m2') else "N/A"
                    ville_str = row.get('ville', 'N/A') or 'N/A'
                    st.markdown(f"""
                    <div class="alerte-card">
                        <b style="color:#FAF7F2;">🏠 {row.get('titre','')[:65]}</b><br><br>
                        <span class="annonce-badge badge-prix">💰 {prix_str}</span>
                        <span class="annonce-badge badge-surface">📐 {surface_str}</span>
                        <span class="annonce-badge badge-ville">🏙️ {ville_str}</span>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    if row.get('url'):
                        st.markdown(f"""
                        <a href="{row['url']}" target="_blank"
                           style="display:block; text-align:center;
                                  background:linear-gradient(135deg,#D4AF37,#C1440E);
                                  color:white; padding:8px 12px; border-radius:8px;
                                  font-weight:600; text-decoration:none;
                                  margin-top:16px; font-size:0.85rem;">👁️ Voir</a>
                        """, unsafe_allow_html=True)
        else:
            st.warning("😔 Aucune annonce ne correspond. Élargissez votre budget.")

    if st.session_state.get("user_email"):
        st.markdown('<div class="separateur">✦ ◆ ✦ ◆ ✦</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📺 Gagnez des crédits gratuits</div>', unsafe_allow_html=True)
        col_pub1, col_pub2 = st.columns(2)
        with col_pub1:
            st.markdown("""
            <div class="pub-card">
                <div style="font-size:1.5rem;">📺</div>
                <b style="color:#D4AF37;">Voir une pub = +1 crédit</b><br>
                <span style="font-size:0.8rem; color:rgba(250,247,242,0.6);">Soutenez Immo Maroc gratuitement</span>
            </div>
            """, unsafe_allow_html=True)
            if st.button("▶️ Voir la pub (+1 crédit)"):
                pub = random.choice(PUBS)
                st.markdown(f"""
                <div class="alerte-card" style="text-align:center;">
                    <b style="color:#D4AF37;">{pub['titre']}</b><br>
                    <span style="font-size:0.85rem;">{pub['desc']}</span><br>
                    <a href="{pub['url']}" target="_blank"
                       style="color:#D4AF37; font-weight:600; text-decoration:none;">
                        {pub['cta']} →</a>
                </div>
                """, unsafe_allow_html=True)
                ajouter_credits(st.session_state["user_email"], 1)
                st.success("✅ +1 crédit ajouté !")
                st.rerun()
        with col_pub2:
            st.markdown("""
            <div class="pub-card">
                <div style="font-size:1.5rem;">📤</div>
                <b style="color:#D4AF37;">Partager = +2 crédits</b><br>
                <span style="font-size:0.8rem; color:rgba(250,247,242,0.6);">Partagez sur WhatsApp</span>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("""
            <a href="https://wa.me/?text=Découvrez Immo Maroc https://maghreb-immo.streamlit.app"
               target="_blank"
               style="display:block; text-align:center;
                      background:linear-gradient(135deg,#25D366,#128C7E);
                      color:white; padding:8px 12px; border-radius:8px;
                      font-weight:600; text-decoration:none; margin-bottom:8px; font-size:0.85rem;">
                📤 Partager sur WhatsApp</a>
            """, unsafe_allow_html=True)
            if st.button("✅ J'ai partagé (+2 crédits)"):
                ajouter_credits(st.session_state["user_email"], 2)
                st.success("✅ +2 crédits ajoutés !")
                st.rerun()

# ════════════════════════════════
# TAB 4
# ════════════════════════════════
with tab4:
    st.markdown('<div class="section-title">💳 Recharger vos crédits</div>', unsafe_allow_html=True)

    if not st.session_state.get("user_email"):
        st.warning("👤 Connectez-vous pour accéder aux packs payants.")
    else:
        email = st.session_state["user_email"]
        credits = get_credits(email)
        st.markdown(f'<div style="margin-bottom:20px;"><span class="credits-badge">💎 Solde actuel : {credits} crédits</span></div>', unsafe_allow_html=True)

        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            st.markdown("""
            <div class="kpi-card" style="border-top:4px solid #52B788;">
                <div style="font-size:1.5rem;">🌱</div>
                <div class="kpi-value" style="color:#52B788;">9,99 €</div>
                <div style="color:#D4AF37; font-weight:600; margin:8px 0;">Pack Starter</div>
                <div style="color:rgba(250,247,242,0.7); font-size:0.85rem; line-height:2;">
                    💎 100 crédits<br>🔍 100 recherches<br>✅ Sans pub</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🌱 Acheter Starter", key="buy_starter"):
                session_stripe = creer_session_paiement(email, "starter")
                if session_stripe:
                    st.markdown(f"""<a href="{session_stripe.url}" target="_blank"
                       style="display:block; text-align:center;
                              background:linear-gradient(135deg,#D4AF37,#C1440E);
                              color:white; padding:10px; border-radius:8px;
                              font-weight:600; text-decoration:none; margin-top:8px;">
                        💳 Payer maintenant →</a>""", unsafe_allow_html=True)

        with col_p2:
            st.markdown("""
            <div class="kpi-card" style="border-top:4px solid #D4AF37;">
                <div style="font-size:1.5rem;">⭐</div>
                <div class="kpi-value">39,99 €</div>
                <div style="color:#D4AF37; font-weight:600; margin:8px 0;">Pack Pro</div>
                <div style="color:rgba(250,247,242,0.7); font-size:0.85rem; line-height:2;">
                    💎 500 crédits<br>🔍 500 recherches<br>✅ Sans pub<br>🔔 Alertes email</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("⭐ Acheter Pro", key="buy_pro"):
                session_stripe = creer_session_paiement(email, "pro")
                if session_stripe:
                    st.markdown(f"""<a href="{session_stripe.url}" target="_blank"
                       style="display:block; text-align:center;
                              background:linear-gradient(135deg,#D4AF37,#C1440E);
                              color:white; padding:10px; border-radius:8px;
                              font-weight:600; text-decoration:none; margin-top:8px;">
                        💳 Payer maintenant →</a>""", unsafe_allow_html=True)

        with col_p3:
            st.markdown("""
            <div class="kpi-card" style="border-top:4px solid #C1440E;">
                <div style="font-size:1.5rem;">🚀</div>
                <div class="kpi-value" style="color:#C1440E;">99,99 €</div>
                <div style="color:#D4AF37; font-weight:600; margin:8px 0;">Pack Business</div>
                <div style="color:rgba(250,247,242,0.7); font-size:0.85rem; line-height:2;">
                    💎 2000 crédits<br>🔍 2000 recherches<br>✅ Sans pub<br>🔔 Alertes email<br>📊 Export Excel</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🚀 Acheter Business", key="buy_business"):
                session_stripe = creer_session_paiement(email, "business")
                if session_stripe:
                    st.markdown(f"""<a href="{session_stripe.url}" target="_blank"
                       style="display:block; text-align:center;
                              background:linear-gradient(135deg,#D4AF37,#C1440E);
                              color:white; padding:10px; border-radius:8px;
                              font-weight:600; text-decoration:none; margin-top:8px;">
                        💳 Payer maintenant →</a>""", unsafe_allow_html=True)

# ── Bannière bas
if not est_payant:
    pub_b = random.choice(PUBS)
    st.markdown(f"""
    <div class="banniere-bas">
        <div style="font-size:0.65rem; color:rgba(212,175,55,0.5);
             text-transform:uppercase; letter-spacing:1px; white-space:nowrap;">Pub</div>
        <div style="color:#FAF7F2; font-size:0.85rem; flex:1; text-align:center; padding:0 12px;">
            {pub_b['texte_banniere']}</div>
        <a href="{pub_b['url']}" target="_blank"
           style="background:linear-gradient(135deg,#D4AF37,#C1440E);
                  color:white; padding:6px 16px; border-radius:6px;
                  font-weight:600; text-decoration:none; font-size:0.8rem; white-space:nowrap;">
            {pub_b['cta_court']}</a>
    </div>
    <div style="height:55px;"></div>
    """, unsafe_allow_html=True)

# ── Footer
st.markdown("""
<div style="text-align:center; padding:30px 0 10px 0; color:#D4AF37; opacity:0.5; font-size:0.85rem;">
    ✦ ◆ ✦ ◆ ✦ ◆ ✦ ◆ ✦<br>
    Immo Maroc © 2026 — Veille intelligente du marché immobilier marocain<br>
    ✦ ◆ ✦ ◆ ✦ ◆ ✦ ◆ ✦
</div>
""", unsafe_allow_html=True)