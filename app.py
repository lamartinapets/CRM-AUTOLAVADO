import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="CRM La Martina Pets", layout="wide", page_icon="🐾")

# --- LOGIN ---
if "auth" not in st.session_state:
    st.title("🔐 Acceso La Martina")
    pw = st.text_input("Contraseña de seguridad", type="password")
    if st.button("Ingresar"):
        if pw == st.secrets["password"]:
            st.session_state["auth"] = True
            st.rerun()
        else:
            st.error("❌ Clave incorrecta")
    st.stop()

# --- CONEXIÓN DIRECTA ---
# ID de tu Excel según tu link: 1rHtwtkyxsyY2mp32sCQ4VRiQ5pLOZpM4jiBs9vbYtmw
URL_CSV = "https://docs.google.com/spreadsheets/d/1rHtwtkyxsyY2mp32sCQ4VRiQ5pLOZpM4jiBs9vbYtmw/export?format=csv&gid=0"

@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(URL_CSV)
        df.columns = [c.strip() for c in df.columns] # Limpiar espacios en nombres
        df['fecha'] = pd.to_datetime(df['fecha'], dayfirst=True, errors='coerce')
        if 'valor' in df.columns:
            df['valor'] = df['valor'].astype(str).replace(r'[\$,]', '', regex=True).astype(float)
        return df
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return None

df = load_data()

# --- INTERFAZ ---
if df is not None:
    st.title("🐾 CRM La Martina Pets")
    
    menu = st.sidebar.selectbox("Menú", ["📊 Reportes", "🔍 Buscador", "📅 Citas de Hoy"])

    if menu == "📊 Reportes":
        st.subheader("Análisis de Ventas y Canales")
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Ventas Totales", f"${df['valor'].sum():,.0f}")
        with c2:
            st.metric("Total Mascotas", len(df))
        
        st.divider()
        col_a, col_b = st.columns(2)
        with col_a:
            st.write("#### Canales que más traen clientes")
            st.bar_chart(df['Canal'].value_counts())
        with col_b:
            st.write("#### Razas más frecuentes")
            st.bar_chart(df['raza'].value_counts().head(5))

    elif menu == "🔍 Buscador":
        st.subheader("Buscador Rápido")
        busqueda = st.text_input("Nombre de mascota, dueño o teléfono")
        if busqueda:
            res = df[df.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)]
            st.dataframe(res, use_container_width=True)
        else:
            st.dataframe(df, use_container_width=True)

    elif menu == "📅 Citas de Hoy":
        st.subheader("Agenda del Día")
        hoy = datetime.now().date()
        df_hoy = df[df['fecha'].dt.date == hoy]
        if not df_hoy.empty:
            st.table(df_hoy[['mascota', 'cliente', 'Canal']])
        else:
            st.info("No hay citas programadas para hoy.")
