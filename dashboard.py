import streamlit as st
import pandas as pd
import plotly.express as px
import folium
import uuid
import random
import os
from streamlit_folium import st_folium

# ── Charger les secrets
try:
    for key in ["GROQ_API_KEY", "STRIPE_PUBLIC_KEY", "STRIPE_SECRET_KEY",
                "DATABASE_URL", "SENDGRID_API_KEY", "SENDGRID_FROM_EMAIL"]:
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
                  get_session_anonyme, utiliser_recherche_anonyme,
                  enregistrer_recherche, changer_mot_de_passe)
from paiement import creer_session_paiement
from email_service import (init_reset_table, envoyer_email_reset,
                           verifier_token_reset, consommer_token_reset,
                           envoyer_email_bienvenue)

VILLES_COORDS = {
    'Casablanca': [33.5731, -7.5898], 'Rabat': [34.0209, -6.8416],
    'Marrakech': [31.6295, -7.9811], 'Fès': [34.0181, -5.0078],
    'Tanger': [35.7595, -5.8340], 'Agadir': [30.4278, -9.5981],
    'Meknès': [33.8935, -5.5473], 'Oujda': [34.6814, -1.9086],
    'Kénitra': [34.2610, -6.5802], 'Tétouan': [35.5785, -5.3684],
    'Salé': [34.0531, -6.7985], 'Nador': [35.1681, -2.9287],
    'Mohammedia': [33.6866, -7.3830], 'El Jadida': [33.2316, -8.5007],
    'Béni Mellal': [32.3373, -6.3498], 'Settat': [33.0010, -7.6197],
    'Temara': [33.9287, -6.9091], 'Bouznika': [33.7914, -7.1586],
    'Guéliz': [31.6340, -8.0089], 'Ain Sebaa': [33.6070, -7.5150],
    'Bouskoura': [33.4500, -7.6500], 'Dar Bouazza': [33.4833, -7.7667],
}

PUBS = [
    {"titre": "🏠 Mubawab.ma", "desc": "Plus de 100 000 annonces immobilières au Maroc",
     "url": "https://www.mubawab.ma", "cta": "Voir →"},
    {"titre": "🔑 Yakeey.com", "desc": "L'immobilier neuf au Maroc",
     "url": "https://www.yakeey.com", "cta": "Découvrir →"},
    {"titre": "🏡 Sarouty.ma", "desc": "Achat, vente, location au Maroc",
     "url": "https://www.sarouty.ma", "cta": "Explorer →"},
    {"titre": "💰 CIH Bank", "desc": "Simulez votre crédit immobilier",
     "url": "https://www.cih.co.ma", "cta": "Simuler →"},
]

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap');

/* ── Cacher header natif Streamlit */
header[data-testid="stHeader"] { display: none !important; }
#MainMenu { display: none !important; }
footer { display: none !important; }
.block-container { padding-top: 0 !important; }

html, body, [class*="css"], .stApp, .main, .block-container {
    background-color: #1B4332 !important;
    font-family: 'Inter', sans-serif;
    color: #FAF7F2 !important;
}

/* ── Header */
.pro-header {
    background: linear-gradient(135deg, #0a1f17 0%, #1B4332 60%, #0d2b1e 100%);
    border-bottom: 2px solid rgba(212,175,55,0.4);
    margin-bottom: 20px;
}
.header-inner {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 24px;
}
.header-logo {
    font-family: 'Playfair Display', serif;
    font-size: 1.6rem;
    font-weight: 700;
    color: #FAF7F2;
    display: flex;
    align-items: center;
    gap: 8px;
}
.header-logo .gold { color: #D4AF37; }
.header-subtitle {
    color: rgba(250,247,242,0.5);
    font-size: 0.72rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    text-align: center;
    flex: 1;
    padding: 0 20px;
}
.credits-pill {
    background: linear-gradient(135deg, #D4AF37, #C1440E);
    color: white !important;
    padding: 5px 14px;
    border-radius: 20px;
    font-weight: 700;
    font-size: 0.85rem;
}
.user-pill {
    background: rgba(82,183,136,0.2);
    border: 1px solid #52B788;
    color: #9AE6B4 !important;
    padding: 5px 14px;
    border-radius: 20px;
    font-size: 0.85rem;
}

/* ── Modal auth */
.auth-modal {
    background: linear-gradient(135deg, #0a1f17, #1B4332);
    border: 1px solid rgba(212,175,55,0.4);
    border-radius: 20px;
    padding: 32px;
    max-width: 480px;
    margin: 0 auto 24px auto;
    box-shadow: 0 25px 60px rgba(0,0,0,0.4);
    animation: slideDown 0.3s ease;
}
@keyframes slideDown {
    from { opacity: 0; transform: translateY(-20px); }
    to { opacity: 1; transform: translateY(0); }
}
.auth-modal-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.5rem;
    color: #D4AF37;
    text-align: center;
    margin-bottom: 20px;
}

/* ── KPI Cards */
.kpi-card {
    background: rgba(255,255,255,0.07);
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    border: 1px solid rgba(212,175,55,0.4);
    border-top: 4px solid #D4AF37;
    margin-bottom: 10px;
}
.kpi-value { font-family: 'Playfair Display', serif; font-size: 2rem; font-weight: 700; color: #D4AF37; }
.kpi-label { font-size: 0.82rem; color: rgba(250,247,242,0.7); text-transform: uppercase; letter-spacing: 1px; margin-top: 4px; }

/* ── Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a1f17 0%, #112b21 100%) !important;
    border-right: 2px solid rgba(212,175,55,0.3) !important;
}
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] div { color: #FAF7F2 !important; }
section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
    background-color: #0a1f17 !important;
    border: 1px solid rgba(212,175,55,0.4) !important;
    border-radius: 8px !important;
}
section[data-testid="stSidebar"] div[data-baseweb="select"] * {
    color: #FAF7F2 !important;
    background-color: transparent !important;
    -webkit-text-fill-color: #FAF7F2 !important;
}
section[data-testid="stSidebar"] div[data-baseweb="select"] svg { fill: #D4AF37 !important; }
section[data-testid="stSidebar"] input[type="number"] {
    background-color: #0a1f17 !important;
    color: #FAF7F2 !important;
    -webkit-text-fill-color: #FAF7F2 !important;
    border: 1px solid rgba(212,175,55,0.4) !important;
    border-radius: 8px !important;
}
section[data-testid="stSidebar"] .stNumberInput > div {
    background-color: #0a1f17 !important;
    border: 1px solid rgba(212,175,55,0.4) !important;
    border-radius: 8px !important;
}
section[data-testid="stSidebar"] .stNumberInput button {
    background-color: #1B4332 !important;
    color: #D4AF37 !important;
    border: none !important;
}
div[data-baseweb="popover"], div[data-baseweb="popover"] * {
    background-color: #0a1f17 !important; color: #FAF7F2 !important;
}
div[data-baseweb="menu"] {
    background-color: #0a1f17 !important;
    border: 1px solid rgba(212,175,55,0.4) !important;
    border-radius: 8px !important;
}
div[role="option"] { background-color: #0a1f17 !important; color: #FAF7F2 !important; }
div[role="option"]:hover { background-color: rgba(212,175,55,0.15) !important; color: #D4AF37 !important; }
div[aria-selected="true"] { background-color: rgba(212,175,55,0.2) !important; color: #D4AF37 !important; }

/* ── Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.06); border-radius: 10px;
    padding: 4px; border: 1px solid rgba(212,175,55,0.2);
}
.stTabs [data-baseweb="tab"] { color: rgba(250,247,242,0.7) !important; border-radius: 8px; padding: 8px 20px; }
.stTabs [aria-selected="true"] { background: linear-gradient(135deg, #D4AF37, #C1440E) !important; color: white !important; }

/* ── Cards */
.annonce-card {
    background: rgba(255,255,255,0.06); border-radius: 12px;
    padding: 16px 20px; margin: 8px 0;
    border: 1px solid rgba(212,175,55,0.2); border-left: 4px solid #D4AF37;
    transition: transform 0.2s, background 0.2s;
}
.annonce-card:hover { transform: translateX(4px); background: rgba(255,255,255,0.1); }
.annonce-titre { font-family: 'Playfair Display', serif; font-size: 1rem; font-weight: 600; color: #FAF7F2; margin-bottom: 10px; }
.annonce-badge { display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 0.78rem; font-weight: 500; margin-right: 6px; margin-top: 4px; }
.badge-prix { background: rgba(212,175,55,0.15); color: #D4AF37; border: 1px solid rgba(212,175,55,0.5); }
.badge-surface { background: rgba(99,179,237,0.15); color: #90CDF4; border: 1px solid rgba(99,179,237,0.4); }
.badge-ville { background: rgba(154,230,180,0.15); color: #9AE6B4; border: 1px solid rgba(154,230,180,0.4); }
.badge-source { background: rgba(252,129,74,0.15); color: #FC814A; border: 1px solid rgba(252,129,74,0.4); }
.alerte-card { background: rgba(212,175,55,0.08); border-radius: 10px; padding: 14px 18px; margin: 8px 0; border: 1px solid rgba(212,175,55,0.3); border-left: 4px solid #D4AF37; }
.section-title { font-family: 'Playfair Display', serif; font-size: 1.3rem; color: #D4AF37; border-bottom: 1px solid rgba(212,175,55,0.3); padding-bottom: 8px; margin-bottom: 16px; }
.separateur { text-align: center; color: #D4AF37; font-size: 1.2rem; letter-spacing: 12px; margin: 20px 0; opacity: 0.5; }
.credits-badge { background: linear-gradient(135deg, #D4AF37, #C1440E); color: white !important; padding: 6px 16px; border-radius: 20px; font-weight: 600; font-size: 0.9rem; display: inline-block; margin: 5px 0; }
.pub-card { background: rgba(212,175,55,0.06); border: 1px dashed rgba(212,175,55,0.4); border-radius: 10px; padding: 14px; text-align: center; margin: 10px 0; }
.lock-card { background: rgba(193,68,14,0.1); border: 1px solid rgba(193,68,14,0.4); border-radius: 12px; padding: 24px; text-align: center; margin: 20px 0; }
.stButton button { background: linear-gradient(135deg, #D4AF37, #C1440E) !important; color: white !important; border: none !important; border-radius: 8px !important; font-weight: 600 !important; width: 100% !important; }
.succes-paiement { background: linear-gradient(135deg, rgba(82,183,136,0.2), rgba(27,67,50,0.8)); border: 1px solid #52B788; border-radius: 12px; padding: 20px; text-align: center; margin-bottom: 20px; }

/* ── Inputs */
input[type="text"], input[type="email"], input[type="password"] {
    background-color: rgba(255,255,255,0.08) !important;
    color: #FAF7F2 !important;
    -webkit-text-fill-color: #FAF7F2 !important;
    border: 1px solid rgba(212,175,55,0.4) !important;
    border-radius: 8px !important;
}

/* ── Footer défilant */
.footer-marquee {
    background: linear-gradient(90deg, #0a1f17 0%, #112b21 50%, #0a1f17 100%);
    border-top: 1px solid rgba(212,175,55,0.4);
    position: fixed;
    bottom: 0; left: 0; right: 0;
    z-index: 1000;
    overflow: hidden;
    height: 44px;
    display: flex;
    align-items: center;
}
.marquee-track {
    display: flex;
    animation: marquee 35s linear infinite;
    white-space: nowrap;
}
.marquee-track:hover { animation-play-state: paused; }
@keyframes marquee {
    0% { transform: translateX(0); }
    100% { transform: translateX(-50%); }
}
.marquee-item {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 0 28px;
    font-size: 0.82rem;
    border-right: 1px solid rgba(212,175,55,0.2);
}
.marquee-item a { color: #D4AF37 !important; text-decoration: none; font-weight: 600; }
.marquee-item span { color: rgba(250,247,242,0.6); }

p, span, label, h1, h2, h3 { color: #FAF7F2 !important; }
</style>
"""


def get_annonces(ville=None, prix_min=None, prix_max=None, surface_min=None, surface_max=None, source=None):
    try:
        conn, db_type = get_db_connection()
        ph = get_placeholder(db_type)
        query = "SELECT * FROM annonces WHERE 1=1"
        params = []
        if ville and ville != "Toutes":
            query += f" AND ville = {ph}"; params.append(ville)
        if prix_min:
            query += f" AND prix_dh >= {ph}"; params.append(prix_min)
        if prix_max:
            query += f" AND prix_dh <= {ph}"; params.append(prix_max)
        if surface_min:
            query += f" AND surface_m2 >= {ph}"; params.append(surface_min)
        if surface_max:
            query += f" AND surface_m2 <= {ph}"; params.append(surface_max)
        if source and source != "Toutes":
            query += f" AND source = {ph}"; params.append(source)
        query += " ORDER BY prix_dh ASC NULLS LAST" if db_type == "postgresql" else " ORDER BY prix_dh ASC"
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df
    except:
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
        query = f"""SELECT titre, prix_dh, surface_m2, prix_m2, ville, url, source
            FROM annonces WHERE prix_dh <= {ph} AND prix_dh IS NOT NULL
            AND surface_m2 >= {ph} AND surface_m2 IS NOT NULL"""
        params = [budget_max, surface_min]
        if ville and ville != "Toutes":
            query += f" AND ville = {ph}"; params.append(ville)
        query += " ORDER BY prix_dh ASC LIMIT 10"
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df
    except:
        return pd.DataFrame()


# ══════════════════════════════════════════════
# INIT
# ══════════════════════════════════════════════
init_auth_db()
init_reset_table()

st.set_page_config(
    page_title="Immo Maroc — Veille Immobilière",
    page_icon="🇲🇦",
    layout="wide"
)
st.markdown(CSS, unsafe_allow_html=True)

# ── Session anonyme
if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())

# ── Gestion reset password
query_params = st.query_params
action = query_params.get("action", "")
reset_token = query_params.get("token", "")
if action == "reset" and reset_token:
    st.session_state["reset_mode"] = True
    st.session_state["reset_token"] = reset_token
    st.query_params.clear()

# ── Retour paiement Stripe
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

user_email = st.session_state.get("user_email")
credits_user = get_credits(user_email) if user_email else 0
est_payant = credits_user > 50

# ══════════════════════════════════════════════
# MODE RESET PASSWORD
# ══════════════════════════════════════════════
if st.session_state.get("reset_mode"):
    token = st.session_state.get("reset_token", "")
    email_reset, msg_token = verifier_token_reset(token)

    col_c = st.columns([1, 2, 1])[1]
    with col_c:
        if email_reset:
            st.markdown(f"""
            <div class="auth-modal">
                <div class="auth-modal-title">🔑 Nouveau mot de passe</div>
                <p style="color:rgba(250,247,242,0.7); text-align:center;">
                    Compte : <b style="color:#D4AF37;">{email_reset}</b>
                </p>
            </div>
            """, unsafe_allow_html=True)
            nouveau_mdp = st.text_input("Nouveau mot de passe", type="password")
            confirm_mdp = st.text_input("Confirmer", type="password")
            if st.button("✅ Changer le mot de passe"):
                if len(nouveau_mdp) < 6:
                    st.error("❌ Minimum 6 caractères")
                elif nouveau_mdp != confirm_mdp:
                    st.error("❌ Mots de passe différents")
                else:
                    changer_mot_de_passe(email_reset, nouveau_mdp)
                    consommer_token_reset(token)
                    st.success("✅ Mot de passe changé !")
                    st.session_state.pop("reset_mode", None)
                    st.session_state.pop("reset_token", None)
                    st.rerun()
        else:
            st.error(msg_token)
            if st.button("Retour"):
                st.session_state.pop("reset_mode", None)
                st.rerun()
    st.stop()

# ══════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════
col_logo, col_sub, col_auth = st.columns([2, 4, 3])

with col_logo:
    st.markdown("""
    <div style="padding:12px 0; display:flex; align-items:center; gap:8px;">
        <span style="font-size:1.8rem;">🇲🇦</span>
        <span style="font-family:'Playfair Display',serif; font-size:1.5rem; font-weight:700; color:#FAF7F2;">
            Immo<span style="color:#D4AF37;">Maroc</span>
        </span>
    </div>
    """, unsafe_allow_html=True)

with col_sub:
    st.markdown("""
    <div style="text-align:center; padding:16px 0; color:rgba(250,247,242,0.45);
         font-size:0.7rem; letter-spacing:3px; text-transform:uppercase;">
        ✦ Veille intelligente du marché immobilier marocain ✦
    </div>
    """, unsafe_allow_html=True)

with col_auth:
    if user_email:
        col_u1, col_u2, col_u3 = st.columns([3, 2, 2])
        with col_u1:
            st.markdown(f'<div style="padding:12px 0;"><span class="user-pill">✅ {user_email.split("@")[0]}</span></div>', unsafe_allow_html=True)
        with col_u2:
            st.markdown(f'<div style="padding:12px 0;"><span class="credits-pill">💎 {credits_user}</span></div>', unsafe_allow_html=True)
        with col_u3:
            if st.button("🚪 Sortir", key="btn_deco"):
                st.session_state.pop("user_email", None)
                st.session_state.pop("resultats_recherche", None)
                st.rerun()
    else:
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("🔐 Connexion", key="btn_login_h"):
                st.session_state["show_auth"] = "connexion"
                st.rerun()
        with col_b2:
            if st.button("✨ S'inscrire", key="btn_reg_h"):
                st.session_state["show_auth"] = "inscription"
                st.rerun()

st.markdown('<hr style="border:none; border-top:1px solid rgba(212,175,55,0.3); margin:0 0 16px 0;">', unsafe_allow_html=True)

# ── Notification paiement
if st.session_state.get("paiement_succes"):
    info = st.session_state["paiement_succes"]
    st.markdown(f"""
    <div class="succes-paiement">
        <div style="font-size:2rem;">🎉</div>
        <div style="font-family:'Playfair Display',serif; font-size:1.3rem; color:#52B788;">Paiement confirmé !</div>
        <div>Pack <b style="color:#D4AF37;">{info['pack'].capitalize()}</b> — <b style="color:#D4AF37;">+{info['credits']} crédits</b></div>
    </div>
    """, unsafe_allow_html=True)
    st.session_state.pop("paiement_succes", None)

# ══════════════════════════════════════════════
# MODAL AUTH (dans la page principale)
# ══════════════════════════════════════════════
if not user_email and st.session_state.get("show_auth"):
    mode_auth = st.session_state["show_auth"]

    col_c = st.columns([1, 2, 1])[1]
    with col_c:
        st.markdown(f"""
        <div class="auth-modal">
            <div class="auth-modal-title">
                {"🔐 Connexion" if mode_auth == "connexion" else "✨ Créer un compte" if mode_auth == "inscription" else "🔑 Mot de passe oublié"}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Tabs
        col_t1, col_t2, col_t3, col_t4 = st.columns(4)
        with col_t1:
            if st.button("🔐 Connexion", key="tab_login"):
                st.session_state["show_auth"] = "connexion"
                st.rerun()
        with col_t2:
            if st.button("✨ Inscription", key="tab_reg"):
                st.session_state["show_auth"] = "inscription"
                st.rerun()
        with col_t3:
            if st.button("🔑 Oublié ?", key="tab_forgot"):
                st.session_state["show_auth"] = "forgot"
                st.rerun()
        with col_t4:
            if st.button("✕ Fermer", key="tab_close"):
                st.session_state.pop("show_auth", None)
                st.rerun()

        st.markdown("---")

        if mode_auth == "connexion":
            email_in = st.text_input("📧 Email", key="m_login_email")
            pwd_in = st.text_input("🔒 Mot de passe", type="password", key="m_login_pwd")
            if st.button("Se connecter →", key="m_btn_login"):
                if email_in and pwd_in:
                    user = connecter_utilisateur(email_in, pwd_in)
                    if user:
                        st.session_state["user_email"] = email_in
                        st.session_state.pop("show_auth", None)
                        st.success("✅ Connecté !")
                        st.rerun()
                    else:
                        st.error("❌ Email ou mot de passe incorrect")

        elif mode_auth == "inscription":
            nom_in = st.text_input("👤 Nom complet", key="m_reg_nom")
            email_in = st.text_input("📧 Email", key="m_reg_email")
            pwd_in = st.text_input("🔒 Mot de passe (min. 6 car.)", type="password", key="m_reg_pwd")
            pwd2_in = st.text_input("🔒 Confirmer", type="password", key="m_reg_pwd2")
            if st.button("Créer mon compte →", key="m_btn_reg"):
                if not all([nom_in, email_in, pwd_in, pwd2_in]):
                    st.error("❌ Remplissez tous les champs")
                elif pwd_in != pwd2_in:
                    st.error("❌ Mots de passe différents")
                elif len(pwd_in) < 6:
                    st.error("❌ Mot de passe trop court")
                else:
                    ok, msg = inscrire_utilisateur(email_in, pwd_in, nom_in)
                    if ok:
                        st.session_state["user_email"] = email_in
                        st.session_state.pop("show_auth", None)
                        envoyer_email_bienvenue(email_in, nom_in)
                        st.success(f"🎉 Bienvenue {nom_in} ! 5 crédits offerts !")
                        st.rerun()
                    else:
                        st.error(msg)

        else:  # forgot
            email_r = st.text_input("📧 Votre email", key="m_forgot_email")
            if st.button("📧 Envoyer le lien →", key="m_btn_forgot"):
                if email_r:
                    ok, msg = envoyer_email_reset(email_r)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)

# ══════════════════════════════════════════════
# SIDEBAR — FILTRES UNIQUEMENT
# ══════════════════════════════════════════════
st.sidebar.markdown("""
<div style="text-align:center; padding:16px 0 10px 0;">
    <div style="font-family:'Playfair Display',serif; font-size:1.1rem; color:#D4AF37; font-weight:600;">
        🔍 Filtres
    </div>
    <div style="height:1px; background:rgba(212,175,55,0.3); margin-top:10px;"></div>
</div>
""", unsafe_allow_html=True)

# Statut utilisateur dans sidebar (lecture seule)
if user_email:
    st.sidebar.markdown(f"""
    <div style="text-align:center; padding:8px; background:rgba(82,183,136,0.1);
         border-radius:10px; border:1px solid rgba(82,183,136,0.3); margin-bottom:12px;">
        <div style="color:#9AE6B4; font-size:0.8rem;">✅ {user_email.split('@')[0]}</div>
        <div class="credits-badge" style="margin-top:4px; font-size:0.8rem;">💎 {credits_user} crédits</div>
    </div>
    """, unsafe_allow_html=True)

st.sidebar.markdown("**🏙️ Ville**")
villes = get_villes()
ville_choisie = st.sidebar.selectbox("Ville", villes, label_visibility="collapsed")

st.sidebar.markdown("**🌐 Source**")
sources = get_sources()
source_choisie = st.sidebar.selectbox("Source", sources, label_visibility="collapsed")

st.sidebar.markdown("**🏠 Type de bien**")
type_choisie = st.sidebar.selectbox("Type", ["Tous", "appartement", "villa", "studio", "terrain", "bureau"], label_visibility="collapsed")

st.sidebar.markdown("**💰 Budget (DH)**")
col_s1, col_s2 = st.sidebar.columns(2)
with col_s1:
    prix_min = st.number_input("Min", min_value=0, value=0, step=50000, label_visibility="collapsed", key="prix_min")
with col_s2:
    prix_max = st.number_input("Max", min_value=0, value=10000000, step=50000, label_visibility="collapsed", key="prix_max")

st.sidebar.markdown("**📐 Surface (m²)**")
col_s3, col_s4 = st.sidebar.columns(2)
with col_s3:
    surface_min = st.number_input("Min", min_value=0, value=0, step=10, label_visibility="collapsed", key="surf_min")
with col_s4:
    surface_max = st.number_input("Max", min_value=0, value=1000, step=10, label_visibility="collapsed", key="surf_max")

st.sidebar.markdown("---")

if not est_payant:
    pub_s = random.choice(PUBS)
    st.sidebar.markdown(f"""
    <div style="background:rgba(212,175,55,0.06); border:1px dashed rgba(212,175,55,0.3);
         border-radius:10px; padding:12px; text-align:center;">
        <div style="font-size:0.6rem; color:rgba(250,247,242,0.35); text-transform:uppercase; letter-spacing:2px; margin-bottom:6px;">Publicité</div>
        <b style="color:#D4AF37; font-size:0.85rem;">{pub_s['titre']}</b><br>
        <span style="font-size:0.75rem; color:rgba(250,247,242,0.6);">{pub_s['desc'][:50]}...</span><br>
        <a href="{pub_s['url']}" target="_blank" style="color:#D4AF37; font-weight:600; text-decoration:none; font-size:0.8rem;">{pub_s['cta']}</a>
    </div>
    """, unsafe_allow_html=True)

st.sidebar.markdown("""
<div style="text-align:center; color:rgba(212,175,55,0.4); font-size:0.75rem; margin-top:12px;">
    ✦ ◆ ✦ ◆ ✦<br>Immo Maroc © 2026
</div>
""", unsafe_allow_html=True)

# ── Données
df = get_annonces(
    ville=ville_choisie,
    prix_min=prix_min if prix_min > 0 else None,
    prix_max=prix_max if prix_max < 10000000 else None,
    surface_min=surface_min if surface_min > 0 else None,
    surface_max=surface_max if surface_max < 1000 else None,
    source=source_choisie,
)
total, avec_prix, prix_moyen, prix_m2_moyen = get_stats()

# ══════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════
tab1, tab2, tab3, tab4 = st.tabs(["📊 Tableau de bord", "🗺️ Carte interactive", "🔔 Alertes & Recherche", "💳 Recharger"])

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

    if not df.empty:
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown('<div class="section-title">📍 Annonces par ville</div>', unsafe_allow_html=True)
            df_v = df[df['ville'].notna()]
            if not df_v.empty:
                fig = px.bar(df_v.groupby('ville').size().reset_index(name='count').sort_values('count', ascending=False).head(10),
                    x='ville', y='count', color='count',
                    color_continuous_scale=[[0,'#2d6a4f'],[0.5,'#D4AF37'],[1,'#C1440E']],
                    labels={'ville':'Ville','count':'Annonces'})
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#FAF7F2',family='Inter'), coloraxis_showscale=False)
                fig.update_xaxes(tickcolor='#FAF7F2', gridcolor='rgba(255,255,255,0.1)')
                fig.update_yaxes(tickcolor='#FAF7F2', gridcolor='rgba(255,255,255,0.1)')
                st.plotly_chart(fig, use_container_width=True)
        with col_g2:
            st.markdown('<div class="section-title">💰 Distribution des prix</div>', unsafe_allow_html=True)
            df_p = df[df['prix_dh'].notna()]
            if not df_p.empty:
                fig = px.histogram(df_p, x='prix_dh', nbins=20,
                    color_discrete_sequence=['#D4AF37'], labels={'prix_dh':'Prix (DH)'})
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#FAF7F2',family='Inter'))
                fig.update_xaxes(tickcolor='#FAF7F2', gridcolor='rgba(255,255,255,0.1)')
                fig.update_yaxes(tickcolor='#FAF7F2', gridcolor='rgba(255,255,255,0.1)')
                st.plotly_chart(fig, use_container_width=True)

        st.markdown('<div class="section-title">📊 Prix vs Surface</div>', unsafe_allow_html=True)
        df_sc = df[df['prix_dh'].notna() & df['surface_m2'].notna()]
        if not df_sc.empty:
            fig = px.scatter(df_sc, x='surface_m2', y='prix_dh', color='ville',
                hover_data=['titre','type_bien'],
                color_discrete_sequence=['#D4AF37','#C1440E','#52B788','#90CDF4','#FC814A','#B794F4'],
                labels={'surface_m2':'Surface (m²)','prix_dh':'Prix (DH)'})
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#FAF7F2',family='Inter'),
                legend=dict(bgcolor='rgba(0,0,0,0)',font=dict(color='#FAF7F2')))
            fig.update_xaxes(tickcolor='#FAF7F2', gridcolor='rgba(255,255,255,0.1)')
            fig.update_yaxes(tickcolor='#FAF7F2', gridcolor='rgba(255,255,255,0.1)')
            st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="separateur">✦ ◆ ✦ ◆ ✦</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-title">📋 Annonces ({len(df)} résultats)</div>', unsafe_allow_html=True)

    if not df.empty:
        for i, (_, row) in enumerate(df.iterrows()):
            if i >= 5 and not user_email:
                st.markdown("""
                <div class="lock-card">
                    <div style="font-size:2rem;">🔒</div>
                    <div style="font-family:'Playfair Display',serif; font-size:1.2rem; color:#D4AF37; margin:8px 0;">Inscrivez-vous gratuitement</div>
                    <div style="color:rgba(250,247,242,0.7); font-size:0.9rem;">5 crédits offerts à l'inscription !</div>
                </div>
                """, unsafe_allow_html=True)
                break
            prix_str = f"{int(row['prix_dh']):,} DH" if pd.notna(row['prix_dh']) else "Prix N/A"
            surface_str = f"{int(row['surface_m2'])} m²" if pd.notna(row['surface_m2']) else "N/A"
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
                <a href="{lien}" target="_blank" style="float:right; color:#D4AF37; font-weight:600; text-decoration:none; font-size:0.85rem;">Voir →</a>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("📭 Aucune annonce disponible.")

with tab2:
    st.markdown('<div class="section-title">🗺️ Carte des annonces par ville</div>', unsafe_allow_html=True)
    carte = folium.Map(location=[31.7917,-7.0926], zoom_start=6, tiles='CartoDB dark_matter')
    if not df.empty:
        df_carte = df[df['ville'].notna() & df['prix_dh'].notna()]
        if not df_carte.empty:
            stats_v = df_carte.groupby('ville').agg(
                nb_annonces=('prix_dh','count'), prix_moyen=('prix_dh','mean'), prix_m2_moyen=('prix_m2','mean')
            ).reset_index()
            for _, row in stats_v.iterrows():
                ville = row['ville']
                if ville in VILLES_COORDS:
                    coords = VILLES_COORDS[ville]
                    nb = int(row['nb_annonces'])
                    pm = int(row['prix_moyen'])
                    pm2 = int(row['prix_m2_moyen']) if pd.notna(row['prix_m2_moyen']) else 0
                    folium.CircleMarker(
                        location=coords, radius=max(10,nb*4),
                        color='#D4AF37', fill=True, fill_color='#52B788', fill_opacity=0.7,
                        popup=folium.Popup(f"""<div style="background:#1B4332;color:#FAF7F2;padding:10px;border-radius:8px;border:1px solid #D4AF37;min-width:180px;">
                            <h4 style="color:#D4AF37;margin:0 0 6px 0;">🕌 {ville}</h4>
                            <b>📦</b> {nb} annonces<br><b>💰</b> {pm:,} DH<br><b>📐</b> {pm2:,} DH/m²</div>""", max_width=250),
                        tooltip=f"🕌 {ville} — {nb} annonces"
                    ).add_to(carte)
    st_folium(carte, width=None, height=500)
    st.caption("💡 Cliquez sur un cercle pour voir les détails.")

with tab3:
    st.markdown('<div class="section-title">🔔 Recherche personnalisée</div>', unsafe_allow_html=True)

    if user_email:
        credits_now = get_credits(user_email)
        st.markdown(f'<div style="margin-bottom:10px;"><span class="credits-badge">💎 {credits_now} crédits</span></div>', unsafe_allow_html=True)
        peut_chercher = credits_now > 0
    else:
        session = get_session_anonyme(st.session_state["session_id"])
        restantes = session[1] if session else 0
        st.info(f"👤 Visiteur anonyme — {restantes} recherche(s) gratuite(s) restante(s)")
        peut_chercher = restantes > 0

    col_a1, col_a2, col_a3 = st.columns(3)
    with col_a1:
        budget_alerte = st.number_input("💰 Budget max (DH)", min_value=100000, max_value=20000000, value=1000000, step=50000)
    with col_a2:
        surface_alerte = st.number_input("📐 Surface min (m²)", min_value=20, max_value=500, value=60, step=10)
    with col_a3:
        ville_alerte = st.selectbox("🏙️ Ville", get_villes(), key="ville_alerte")

    if peut_chercher:
        if st.button("🔍 Lancer la recherche (1 crédit)", type="primary"):
            credit_ok = utiliser_credit(user_email) if user_email else utiliser_recherche_anonyme(st.session_state["session_id"])
            if not credit_ok:
                st.error("❌ Plus de crédits !")
            else:
                enregistrer_recherche(email=user_email, session_id=st.session_state["session_id"],
                                     ville=ville_alerte, budget_max=budget_alerte, surface_min=surface_alerte)
                df_res = get_alertes(budget_alerte, surface_alerte, ville_alerte)
                st.session_state["resultats_recherche"] = df_res.to_dict('records') if not df_res.empty else []
                st.rerun()
    else:
        st.markdown("""<div class="lock-card"><div style="font-size:2rem;">🔒</div>
            <div style="font-family:'Playfair Display',serif;font-size:1.2rem;color:#D4AF37;margin:8px 0;">Plus de recherches</div>
            <div style="color:rgba(250,247,242,0.7);font-size:0.9rem;">Inscrivez-vous ou rechargez vos crédits</div></div>""", unsafe_allow_html=True)

    if "resultats_recherche" in st.session_state:
        resultats = st.session_state["resultats_recherche"]
        if resultats:
            st.success(f"✅ {len(resultats)} annonce(s) trouvée(s) !")
            for row in resultats:
                col1, col2 = st.columns([4,1])
                with col1:
                    st.markdown(f"""<div class="alerte-card">
                        <b style="color:#FAF7F2;">🏠 {row.get('titre','')[:65]}</b><br><br>
                        <span class="annonce-badge badge-prix">💰 {f"{int(row['prix_dh']):,} DH" if row.get('prix_dh') else 'N/A'}</span>
                        <span class="annonce-badge badge-surface">📐 {f"{int(row['surface_m2'])} m²" if row.get('surface_m2') else 'N/A'}</span>
                        <span class="annonce-badge badge-ville">🏙️ {row.get('ville','N/A') or 'N/A'}</span>
                    </div>""", unsafe_allow_html=True)
                with col2:
                    if row.get('url'):
                        st.markdown(f"""<a href="{row['url']}" target="_blank"
                            style="display:block;text-align:center;background:linear-gradient(135deg,#D4AF37,#C1440E);
                            color:white;padding:8px;border-radius:8px;font-weight:600;text-decoration:none;margin-top:16px;">👁️ Voir</a>""", unsafe_allow_html=True)
        else:
            st.warning("😔 Aucune annonce ne correspond.")

    if user_email:
        st.markdown('<div class="separateur">✦ ◆ ✦ ◆ ✦</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📺 Gagnez des crédits gratuits</div>', unsafe_allow_html=True)
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.markdown("""<div class="pub-card"><div style="font-size:1.5rem;">📺</div>
                <b style="color:#D4AF37;">Voir une pub = +1 crédit</b><br>
                <span style="font-size:0.8rem;color:rgba(250,247,242,0.6);">Soutenez Immo Maroc</span></div>""", unsafe_allow_html=True)
            if st.button("▶️ Voir la pub (+1 crédit)"):
                pub = random.choice(PUBS)
                st.markdown(f"""<div class="alerte-card" style="text-align:center;">
                    <b style="color:#D4AF37;">{pub['titre']}</b><br>
                    <span>{pub['desc']}</span><br>
                    <a href="{pub['url']}" target="_blank" style="color:#D4AF37;font-weight:600;text-decoration:none;">{pub['cta']}</a>
                </div>""", unsafe_allow_html=True)
                ajouter_credits(user_email, 1)
                st.success("✅ +1 crédit !")
                st.rerun()
        with col_p2:
            st.markdown("""<div class="pub-card"><div style="font-size:1.5rem;">📤</div>
                <b style="color:#D4AF37;">Partager = +2 crédits</b><br>
                <span style="font-size:0.8rem;color:rgba(250,247,242,0.6);">Partagez sur WhatsApp</span></div>""", unsafe_allow_html=True)
            st.markdown("""<a href="https://wa.me/?text=Découvrez Immo Maroc https://maghreb-immo.streamlit.app" target="_blank"
                style="display:block;text-align:center;background:linear-gradient(135deg,#25D366,#128C7E);
                color:white;padding:8px;border-radius:8px;font-weight:600;text-decoration:none;margin-bottom:8px;">📤 WhatsApp</a>""", unsafe_allow_html=True)
            if st.button("✅ J'ai partagé (+2 crédits)"):
                ajouter_credits(user_email, 2)
                st.success("✅ +2 crédits !")
                st.rerun()

with tab4:
    st.markdown('<div class="section-title">💳 Recharger vos crédits</div>', unsafe_allow_html=True)

    if not user_email:
        st.warning("👤 Connectez-vous pour accéder aux packs payants.")
    else:
        credits_now = get_credits(user_email)
        st.markdown(f'<div style="margin-bottom:20px;"><span class="credits-badge">💎 Solde : {credits_now} crédits</span></div>', unsafe_allow_html=True)

        col_p1, col_p2, col_p3 = st.columns(3)
        packs = [
            ("🌱", "Starter", "9,99 €", "starter", "#52B788", "100 crédits", "100 recherches", "Sans pub"),
            ("⭐", "Pro", "39,99 €", "pro", "#D4AF37", "500 crédits", "500 recherches", "Sans pub + alertes"),
            ("🚀", "Business", "99,99 €", "business", "#C1440E", "2000 crédits", "2000 recherches", "Sans pub + export"),
        ]
        for col, (icon, nom, prix, pack_id, couleur, c1, c2, c3) in zip([col_p1, col_p2, col_p3], packs):
            with col:
                st.markdown(f"""
                <div class="kpi-card" style="border-top:4px solid {couleur};">
                    <div style="font-size:1.5rem;">{icon}</div>
                    <div class="kpi-value" style="color:{couleur};">{prix}</div>
                    <div style="color:#D4AF37;font-weight:600;margin:8px 0;">Pack {nom}</div>
                    <div style="color:rgba(250,247,242,0.7);font-size:0.85rem;line-height:2;">
                        💎 {c1}<br>🔍 {c2}<br>✅ {c3}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"{icon} Acheter {nom}", key=f"buy_{pack_id}"):
                    session_stripe = creer_session_paiement(user_email, pack_id)
                    if session_stripe:
                        st.markdown(f"""<a href="{session_stripe.url}" target="_blank"
                            style="display:block;text-align:center;background:linear-gradient(135deg,#D4AF37,#C1440E);
                            color:white;padding:10px;border-radius:8px;font-weight:600;text-decoration:none;margin-top:8px;">
                            💳 Payer maintenant →</a>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# FOOTER DÉFILANT
# ══════════════════════════════════════════════
pubs_footer = PUBS * 4
items_html = ""
for pub in pubs_footer:
    items_html += f"""
    <span class="marquee-item">
        <span>✦</span>
        <span>{pub['titre']}</span>
        <span>—</span>
        <span>{pub['desc'][:45]}</span>
        <a href="{pub['url']}" target="_blank">{pub['cta']}</a>
    </span>
    """

st.markdown(f"""
<div class="footer-marquee">
    <div class="marquee-track">
        {items_html}
        {items_html}
    </div>
</div>
<div style="height:50px;"></div>
""", unsafe_allow_html=True)