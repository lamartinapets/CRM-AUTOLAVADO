import streamlit as st
import pandas as pd

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="CRM La Martina Pets", layout="centered", page_icon="🐾")

# --- LOGIN SEGURO ---
if "auth" not in st.session_state:
    st.title("🔐 Acceso La Martina Pets")
    pass_input = st.text_input("Introduce la contraseña", type="password")
    if st.button("Entrar"):
        # Compara con el secreto 'password'
        if pass_input == st.secrets["password"]:
            st.session_state["auth"] = True
            st.rerun()
        else:
            st.error("❌ Contraseña incorrecta")
    st.stop()

# --- CARGA DE DATOS ---
@st.cache_data(ttl=600)
def load_data():
    try:
        # Extraemos la URL de los Secrets
        raw_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        
        # Si Streamlit detecta una lista, usamos el primer elemento
        s_url = raw_url if isinstance(raw_url, list) else str(raw_url)
        
        # Limpieza de espacios o saltos de línea invisibles
        s_url = s_url.strip().replace('\n', '').replace('\r', '')
        
        # Convertimos a link de descarga directa CSV
        if "/d/" in s_url:
            doc_id = s_url.split("/d/").split("/")
            csv_url = f"https://docs.google.com/spreadsheets/d/{doc_id}/export?format=csv"
        else:
            csv_url = s_url
            
        return pd.read_csv(csv_url)
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

# --- CUERPO DE LA APP ---
st.title("🐾 CRM La Martina Pets")
st.write("Bienvenido al sistema de gestión.")

df = load_data()

if df is not None:
    st.success("✅ ¡Base de datos conectada!")
    
    # Buscador de clientes
    busqueda = st.text_input("🔍 Buscar cliente o mascota...")
    
    if busqueda:
        # Filtro en toda la tabla
        mask = df.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)
        st.dataframe(df[mask], use_container_width=True)
    else:
        st.dataframe(df, use_container_width=True)
else:
    st.warning("⚠️ No se pudo cargar la información. Revisa los permisos del Excel.")
