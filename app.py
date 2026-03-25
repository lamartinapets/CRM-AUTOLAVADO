import streamlit as st
import pandas as pd

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="CRM La Martina Pets", layout="centered", page_icon="🐾")

# --- LOGIN SEGURO ---
def check_password():
    if "password_correct" not in st.session_state:
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

# --- CONEXIÓN A DATOS ---
@st.cache_data(ttl=600)
def load_data():
    try:
        # Forzamos la URL a ser un texto (string) para evitar el error de 'list'
        raw_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        sheet_url = str(raw_url) if isinstance(raw_url, list) else str(raw_url)
        
        # Convertimos el link para descarga directa de datos
        if "docs.google.com" in sheet_url:
            id_excel = sheet_url.split("/d/").split("/")
            csv_url = f"https://docs.google.com/spreadsheets/d/{id_excel}/export?format=csv"
        else:
            csv_url = sheet_url
            
        return pd.read_csv(csv_url)
    except Exception as e:
        st.error(f"Error en formato de datos: {e}")
        return None

# --- CUERPO DE LA APP ---
st.title("🐾 CRM La Martina Pets")
st.write("Bienvenido al sistema de gestión.")

df = load_data()

if df is not None:
    st.success("✅ ¡Base de datos cargada!")
    
    # Buscador
    busqueda = st.text_input("🔍 Buscar cliente o mascota")
    
    if busqueda:
        mask = df.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)
        df_mostrar = df[mask]
    else:
        df_mostrar = df
        
    st.dataframe(df_mostrar, use_container_width=True)
else:
    st.warning("⚠️ No se pudo cargar la información. Revisa los permisos del Excel.")
