import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="CRM La Martina Pets", layout="wide", page_icon="🐾")

# --- LOGIN ---
if "auth" not in st.session_state:
    st.title("🔐 Acceso Administrativo")
    pw = st.text_input("Ingrese la clave", type="password")
    if st.button("Entrar"):
        if pw == st.secrets["password"]:
            st.session_state["auth"] = True
            st.rerun()
    st.stop()

# --- CONEXIÓN ---
# ID de tu Excel según tus capturas
SHEET_ID = "1rHtwtkyxsyY2mp32sCQ4VRiQ5pLOZpM4jiBs9vbYtmw"
URL_CSV = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"

@st.cache_data(ttl=5) # Actualización rápida para ver cambios
def load_data():
    try:
        df = pd.read_csv(URL_CSV)
        df.columns = [c.strip() for c in df.columns]
        df['fecha'] = pd.to_datetime(df['fecha'], dayfirst=True, errors='coerce')
        if 'Canal' in df.columns:
            df['Canal'] = df['Canal'].str.title() # Corrige el error de "Tiktok/TikTok"
        return df
    except:
        return None

df = load_data()

# --- MENÚ PRINCIPAL ---
st.title("🐾 CRM La Martina Pets")
menu = st.sidebar.radio("Navegación", ["📅 Agendar y Citas", "🔍 Buscador e Historial", "📈 Reportes"])

if menu == "📅 Agendar y Citas":
    st.subheader("Gestión de Agenda")
    
    # Pestaña para ver lo de hoy
    hoy = datetime.now().date()
    citas_hoy = df[df['fecha'].dt.date == hoy]
    
    st.write(f"### Citas para hoy: {hoy.strftime('%d/%m/%Y')}")
    if not citas_hoy.empty:
        st.dataframe(citas_hoy[['mascota', 'cliente', 'id', 'Canal']], use_container_width=True)
    else:
        st.info("No hay citas para hoy.")

    st.divider()
    st.write("### 🆕 Para crear una nueva cita:")
    st.info("Debido a los bloqueos de Google en tu cuenta, para agregar un nuevo cliente debes registrarlo en tu archivo de Excel. El CRM lo mostrará aquí automáticamente en 5 segundos.")
    st.link_button("Abrir mi Excel para Agendar", f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit")

elif menu == "🔍 Buscador e Historial":
    st.subheader("Historial de Visitas")
    busqueda = st.text_input("Ingrese nombre de la mascota o dueño para ver su historial")
    
    if busqueda:
        # Filtrar historial
        historial = df[df.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)]
        if not historial.empty:
            st.write(f"Se encontraron {len(historial)} visitas:")
            # Ordenar por fecha más reciente
            st.dataframe(historial.sort_values('fecha', ascending=False), use_container_width=True)
        else:
            st.warning("No se encontró historial para ese nombre.")

elif menu == "📈 Reportes":
    st.subheader("Análisis de Negocio")
    col1, col2 = st.columns(2)
    col1.metric("Ventas Totales", f"${df['valor'].sum():,.0f}")
    col2.metric("Total de Baños", len(df))
    st.bar_chart(df['Canal'].value_counts())
