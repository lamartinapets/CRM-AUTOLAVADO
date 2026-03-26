import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="CRM La Martina Pets", layout="wide", page_icon="🐾")

# --- LOGIN (SEGURIDAD DE LA APP) ---
if "auth" not in st.session_state:
    st.title("🔐 Acceso Administrativo")
    pw = st.text_input("Ingrese la contraseña de seguridad", type="password")
    if st.button("Entrar"):
        if pw == st.secrets["password"]:
            st.session_state["auth"] = True
            st.rerun()
        else:
            st.error("Contraseña incorrecta")
    st.stop()

# --- PANEL DE CONTROL ---
st.title("🐾 CRM Privado - La Martina Pets")

try:
    # Creamos la conexión segura usando los Secrets de [connections.gsheets]
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # Leemos la pestaña 'visitas' que vimos en tu Excel
    # El parámetro 'ttl=0' asegura que siempre veas los datos más recientes
    df = conn.read(
        spreadsheet=st.secrets["connections"]["gsheets"]["spreadsheet"],
        worksheet="visitas",
        ttl=0
    )
    
    st.success("✅ Datos cargados con seguridad privada")

    # --- BUSCADOR ---
    busqueda = st.text_input("🔍 Buscar por mascota, cliente o teléfono...", placeholder="Escribe aquí...")
    
    if busqueda:
        # Filtramos en todas las columnas sin importar mayúsculas
        resultado = df[df.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)]
        st.dataframe(resultado, use_container_width=True, hide_index=True)
        st.info(f"Se encontraron {len(resultado)} registros.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"⚠️ Error de acceso seguro: {str(e)}")
    st.info("Asegúrate de que 'martina-bot@crm-martina-490822.iam.gserviceaccount.com' siga como EDITOR en tu Google Sheet.")

# --- BOTÓN DE ACTUALIZACIÓN ---
if st.button("🔄 Refrescar base de datos"):
    st.cache_data.clear()
    st.rerun()
