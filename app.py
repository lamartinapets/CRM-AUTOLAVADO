import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="CRM La Martina", layout="wide")

# --- LOGIN ---
if "auth" not in st.session_state:
    pw = st.sidebar.text_input("Contraseña", type="password")
    if st.sidebar.button("Entrar"):
        if pw == st.secrets["password"]:
            st.session_state["auth"] = True
            st.rerun()
    st.stop()

# --- CONEXIÓN ---
try:
    # Intenta conexión privada (requiere private_key en Secrets)
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=st.secrets["connections"]["gsheets"]["spreadsheet"], worksheet="visitas")
    st.success("✅ Conexión Privada Exitosa")
except Exception:
    # Si falla por la llave bloqueada, usa lectura pública directa
    url = st.secrets["connections"]["gsheets"]["spreadsheet"].replace('/edit#gid=', '/export?format=csv&gid=')
    df = pd.read_csv(url)
    st.warning("⚠️ Modo Lectura Pública (Llave de Google Bloqueada)")

st.dataframe(df, use_container_width=True)
