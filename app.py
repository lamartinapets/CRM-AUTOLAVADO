import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="CRM La Martina", layout="wide")

# --- LOGIN ---
if "auth" not in st.session_state:
    st.title("🔐 Acceso La Martina")
    pw = st.text_input("Contraseña", type="password")
    if st.button("Entrar"):
        if pw == st.secrets["password"]:
            st.session_state["auth"] = True
            st.rerun()
        else:
            st.error("Incorrecta")
    st.stop()

# --- CONEXIÓN DIRECTA ---
# Usamos el ID de tu hoja que aparece en tus capturas
SHEET_ID = "1rHtwtskyxyY2mp32sCQ4VRiQ5pLOZpM4jiBs9vbYtmw"
SHEET_NAME = "visitas"
url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

@st.cache_data(ttl=0)
def load_data():
    # Esta forma de lectura evita el error de MalformedError
    df = pd.read_csv(url)
    # Ajuste de columnas según tu imagen 9
    df['fecha'] = pd.to_datetime(df['fecha'], dayfirst=True, errors='coerce')
    if 'asistencia' not in df.columns:
        df['asistencia'] = "Pendiente"
    return df

try:
    df = load_data()
except Exception as e:
    st.error("Error de conexión. Verifica que el Excel esté compartido como 'Cualquier persona con el enlace'.")
    st.stop()

# --- INTERFAZ ---
st.title("🐾 CRM Pro - La Martina")

menu = st.sidebar.selectbox("Menú", ["Agenda", "Análisis", "Buscador"])

if menu == "Agenda":
    st.subheader("Citas de Hoy")
    hoy = datetime.now().strftime('%Y-%m-%d')
    hoy_df = df[df['fecha'].dt.strftime('%Y-%m-%d') == hoy]
    
    if not hoy_df.empty:
        st.write("Registros para hoy:")
        st.dataframe(hoy_df[['mascota', 'cliente', 'asistencia']], use_container_width=True)
    else:
        st.info("No hay citas programadas para hoy en el Excel.")

elif menu == "Análisis":
    st.subheader("Comportamiento de Clientes")
    col1, col2 = st.columns(2)
    with col1:
        st.write("### Canales más efectivos")
        st.bar_chart(df['Canal'].value_counts()) # Columna G de tu imagen
    with col2:
        st.write("### Top Razas")
        st.bar_chart(df['raza'].value_counts()) # Columna B de tu imagen

else:
    st.subheader("Buscador de Clientes")
    search = st.text_input("Buscar mascota o cliente")
    if search:
        res = df[df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
        st.dataframe(res, use_container_width=True)
    else:
        st.dataframe(df, use_container_width=True)
