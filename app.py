import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="CRM La Martina Pets", layout="wide", page_icon="🐾")

# --- LOGIN ---
if "auth" not in st.session_state:
    st.title("🔐 Acceso La Martina")
    pw = st.text_input("Ingrese la clave", type="password")
    if st.button("Entrar"):
        if pw == st.secrets["password"]:
            st.session_state["auth"] = True
            st.rerun()
    st.stop()

# --- CONEXIÓN DIRECTA ---
SHEET_ID = "1rHtwtkyxsyY2mp32sCQ4VRiQ5pLOZpM4jiBs9vbYtmw"
URL_CSV = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"

@st.cache_data(ttl=5)
def load_data():
    try:
        df = pd.read_csv(URL_CSV)
        df.columns = [c.strip() for c in df.columns]
        
        # 1. Limpieza de FECHAS
        df['fecha'] = pd.to_datetime(df['fecha'], dayfirst=True, errors='coerce')
        
        # 2. Limpieza de VALOR (Corrige el ValueError de tu imagen)
        if 'valor' in df.columns:
            df['valor'] = df['valor'].astype(str).replace(r'[\$,\.]', '', regex=True)
            df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
            
        # 3. Unificación de TIKTOK (Corrige las dos columnas)
        if 'Canal' in df.columns:
            df['Canal'] = df['Canal'].str.strip().str.capitalize()
            df['Canal'] = df['Canal'].replace({'Tiktok': 'TikTok'})
            
        return df
    except:
        return None

df = load_data()

# --- INTERFAZ ---
st.title("🐾 CRM La Martina Pets")

if df is not None:
    menu = st.sidebar.radio("Navegación", ["📅 Citas de Hoy", "🔍 Buscador e Historial", "📈 Reportes"])

    if menu == "📅 Citas de Hoy":
        st.subheader("Agenda para el día")
        hoy = datetime.now().date()
        # Filtramos por fecha actual
        df_hoy = df[df['fecha'].dt.date == hoy]
        
        if not df_hoy.empty:
            st.dataframe(df_hoy[['mascota', 'cliente', 'id', 'Canal']], use_container_width=True)
        else:
            st.info(f"No hay citas registradas para hoy ({hoy.strftime('%d/%m/%Y')})")
        
        st.divider()
        st.link_button("➕ Abrir Excel para agendar nuevo", f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit")

    elif menu == "🔍 Buscador e Historial":
        st.subheader("Historial Completo")
        busqueda = st.text_input("Buscar mascota o dueño")
        if busqueda:
            # Busca en todas las columnas
            resultado = df[df.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)]
            st.write(f"Resultados: {len(resultado)}")
            st.dataframe(resultado.sort_values('fecha', ascending=False), use_container_width=True)
        else:
            st.dataframe(df.sort_values('fecha', ascending=False), use_container_width=True)

    elif menu == "📈 Reportes":
        st.subheader("Análisis de Negocio")
        col1, col2 = st.columns(2)
        
        # Suma segura de valores
        total_ventas = df['valor'].sum()
        col1.metric("Ventas Totales", f"${total_ventas:,.0f}")
        col2.metric("Total Mascotas", len(df))
        
        st.divider()
        c_a, c_b = st.columns(2)
        with c_a:
            st.write("#### Efectividad de Canales")
            st.bar_chart(df['Canal'].value_counts())
        with c_b:
            st.write("#### Top 5 Razas")
            st.bar_chart(df['raza'].value_counts().head(5))
