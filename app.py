import streamlit as st
import pandas as pd
import gspread
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="CRM La Martina Pets", layout="wide")

# --- LOGIN SEGURO ---
def check_password():
    if "password_correct" not in st.session_state:
        st.title("🔐 Acceso Restringido")
        password = st.text_input("Contraseña", type="password")
        if st.button("Entrar"):
            if password == st.secrets["password"]:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("❌ Contraseña incorrecta")
        return False
    return True

if not check_password():
    st.stop()

# --- CONEXIÓN PRIVADA ---
def load_data():
    try:
        # Usamos el link privado de tus Secrets
        sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        # Conexión via gspread (usa la autenticación de Streamlit de fondo)
        gc = gspread.public_with_link(sheet_url) # Solo funciona si el bot tiene permiso
        # Para máxima seguridad con Service Account, se usa:
        # df = pd.read_csv(f"{sheet_url.replace('/edit', '/export?format=csv')}")
        # Pero lo ideal es usar la URL de exportación privada:
        url = sheet_url.replace('/edit#gid=', '/export?format=csv&gid=')
        return pd.read_csv(url)
    except Exception as e:
        st.error(f"Error de acceso: {e}")
        return None

# --- APP PRINCIPAL ---
st.title("🐾 CRM La Martina Pets")
df = load_data()

if df is not None:
    st.write("### Base de Datos de Clientes")
    st.dataframe(df, use_container_width=True)
