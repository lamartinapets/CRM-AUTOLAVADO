import streamlit as st
import pandas as pd

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="CRM La Martina Pets", layout="wide", page_icon="🐾")

# --- LOGIN SEGURO ---
def check_password():
    if "password_correct" not in st.session_state:
        st.markdown("<br><br>", unsafe_allow_html=True)
        # CORRECCIÓN: Definimos 3 columnas para centrar el login
        col1, col2, col3 = st.columns()
        with col2:
            st.title("🔐 Acceso Restringido")
            st.subheader("La Martina Pets - CRM")
            password = st.text_input("Introduce la contraseña", type="password")
            if st.button("Entrar"):
                # Se usa la contraseña configurada en tus Secrets
                if password == st.secrets["password"]:
                    st.session_state["password_correct"] = True
                    st.rerun()
                else:
                    st.error("❌ Contraseña incorrecta")
        return False
    return True

if not check_password():
    st.stop()

# --- CONEXIÓN SEGURA A DATOS ---
@st.cache_data(ttl=600)
def load_data():
    try:
        # Usa la URL de tu Excel guardada en los Secrets
        sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        # Limpieza de la URL para exportación directa
        base_url = sheet_url.split("/edit")
        csv_url = f"{base_url}/export?format=csv"
        return pd.read_csv(csv_url)
    except Exception as e:
        st.error(f"Error al conectar con los datos: {e}")
        return None

# --- CUERPO DE LA APP ---
st.title("🐾 CRM La Martina Pets")
df = load_data()

if df is not None:
    st.success("✅ Base de datos conectada con éxito")
    
    # Buscador para filtrar clientes
    busqueda = st.text_input("🔍 Buscar cliente (Nombre, ID o Mascota)")
    if busqueda:
        # Filtra en todas las columnas
        df_mostrar = df[df.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)]
    else:
        df_mostrar = df
        
    st.dataframe(df_mostrar, use_container_width=True)
else:
    st.info("No se pudieron cargar los datos. Verifica que el Excel tenga permisos de lectura para quienes tienen el link.")
