import streamlit as st
import pandas as pd
import re
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="CRM La Martina Pets", layout="wide", page_icon="🐾")

# --- LOGIN SEGURO ---
def check_password():
    if "password_correct" not in st.session_state:
        st.markdown("<br><br>", unsafe_allow_index=True)
        col1, col2, col3 = st.columns()
        with col2:
            st.title("🔐 Acceso Restringido")
            st.subheader("La Martina Pets - CRM")
            password = st.text_input("Introduce la contraseña", type="password")
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

# --- CONEXIÓN SEGURA A LOS DATOS ---
@st.cache_data(ttl=600)
def load_data():
    try:
        # Extraemos la URL de tus Secrets
        sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        # Convertimos el link a formato de exportación CSV para lectura privada
        csv_url = sheet_url.replace('/edit#gid=', '/export?format=csv&gid=')
        if '/edit' in csv_url and '/export' not in csv_url:
            csv_url = csv_url.replace('/edit', '/export?format=csv')
            
        return pd.read_csv(csv_url)
    except Exception as e:
        st.error(f"Error al conectar con la base de datos: {e}")
        return None

# --- CUERPO DE LA APP ---
st.title("🐾 CRM La Martina Pets")
df = load_data()

if df is not None:
    st.success("✅ Base de datos cargada correctamente")
    
    # Buscador sencillo
    busqueda = st.text_input("🔍 Buscar cliente (Nombre o ID)")
    if busqueda:
        df_mostrar = df[df.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)]
    else:
        df_mostrar = df
        
    st.dataframe(df_mostrar, use_container_width=True)
else:
    st.info("No se pudieron cargar los datos. Verifica los permisos del archivo.")
