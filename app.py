import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="CRM La Martina Pets", layout="wide")

# --- CONEXIÓN DIRECTA (Sin librerías fallidas) ---
def conectar_gsheets():
    # Usamos los secretos de Streamlit
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    # Intentamos conectar con la URL pública para lectura simple
    sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
    csv_url = sheet_url.replace("/edit#gid=", "/export?format=csv&gid=")
    return pd.read_csv(csv_url)

# --- LOGIN ---
if "auth" not in st.session_state:
    st.title("🔐 Acceso La Martina Pets")
    pass_input = st.text_input("Contraseña", type="password")
    if st.button("Entrar"):
        if pass_input == st.secrets["password"]:
            st.session_state["auth"] = True
            st.rerun()
        else:
            st.error("Incorrecta")
    st.stop()

# --- APP ---
st.title("🐾 CRM La Martina Pets")

try:
    df = conectar_gsheets()
    st.success("✅ Conectado a Google Sheets")
    
    menu = st.sidebar.radio("Menú", ["Ver Clientes", "Registrar"])
    
    if menu == "Ver Clientes":
        st.dataframe(df)
        
except Exception as e:
    st.error(f"Error de conexión: {e}")
    st.info("Asegúrate de que el Google Sheet tenga el acceso 'Cualquier persona con el enlace puede leer'.")
