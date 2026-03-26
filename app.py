import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="CRM La Martina Pets", layout="wide", page_icon="🐾")

# --- LOGIN ---
if "auth" not in st.session_state:
    st.title("🔐 Acceso La Martina")
    pw = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        if pw == st.secrets["password"]:
            st.session_state["auth"] = True
            st.rerun()
    st.stop()

# --- CARGA DE DATOS ---
SHEET_ID = "1rHtwtkyxsyY2mp32sCQ4VRiQ5pLOZpM4jiBs9vbYtmw"
URL_CSV = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"

@st.cache_data(ttl=5)
def load_data():
    try:
        df = pd.read_csv(URL_CSV)
        df.columns = [c.strip() for c in df.columns]
        df['fecha'] = pd.to_datetime(df['fecha'], dayfirst=True, errors='coerce')
        
        # Limpieza de VALOR
        if 'valor' in df.columns:
            df['valor'] = df['valor'].astype(str).replace(r'[\$,\.]', '', regex=True)
            df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
            
        # Unificación de Canales
        if 'Canal' in df.columns:
            df['Canal'] = df['Canal'].str.strip().str.capitalize().replace({'Tiktok': 'TikTok'})
            
        return df
    except:
        return None

df = load_data()

# --- INTERFAZ ---
if df is not None:
    st.title("🐾 CRM La Martina Pets")
    
    menu = st.sidebar.radio("Menú Principal", ["📈 Dashboard de Salud", "🔍 Buscador e Historial", "📅 Citas de Hoy"])

    if menu == "📈 Dashboard de Salud":
        st.subheader("Estado de la Cartera de Clientes")
        
        # Lógica de clasificación (30 días Activos)
        hoy = datetime.now()
        ultimo_contacto = df.groupby('mascota')['fecha'].max().reset_index()
        
        def clasificar(fecha):
            if pd.isna(fecha): return "Sin datos"
            dias = (hoy - fecha).days
            if dias <= 30: return "Activo (Fiel)"
            if dias <= 60: return "Medio (Riesgo)"
            return "Perdido (Inactivo)"

        ultimo_contacto['Estado'] = ultimo_contacto['fecha'].apply(clasificar)
        
        # 1. KPIs Superiores
        k1, k2, k3 = st.columns(3)
        k1.metric("Ingresos Totales", f"${df['valor'].sum():,.0f}")
        k2.metric("Servicios (Visitas)", len(df))
        k3.metric("Mascotas Reales", len(ultimo_contacto))

        st.divider()

        # 2. Gráfico de Barras de Salud
        st.write("#### 📊 Distribución por Fidelidad (Días desde última visita)")
        orden = ["Activo (Fiel)", "Medio (Riesgo)", "Perdido (Inactivo)"]
        stats_salud = ultimo_contacto['Estado'].value_counts().reindex(orden).fillna(0)
        st.bar_chart(stats_salud)

        st.divider()

        # 3. Gráfico de Canales
        st.write("#### 📢 Clientes por Canal de Captación")
        if 'Canal' in df.columns:
            st.bar_chart(df['Canal'].value_counts())

        st.divider()
        
        # 4. Tabla de Clientes para recuperar
        st.write("### 🚨 Clientes Perdidos (Más de 60 días sin venir)")
        perdidos = ultimo_contacto[ultimo_contacto['Estado'] == "Perdido (Inactivo)"]
        # Cruzamos datos para obtener el ID (teléfono)
        info_p = pd.merge(perdidos, df[['mascota', 'cliente', 'id']], on='mascota', how='left').drop_duplicates('mascota')
        st.dataframe(info_p[['mascota', 'cliente', 'id', 'fecha']], use_container_width=True)

    elif menu == "🔍 Buscador e Historial":
        st.subheader("Historial de Visitas")
        busqueda = st.text_input("Nombre de mascota o cliente")
        if busqueda:
            res = df[df.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)]
            st.dataframe(res.sort_values('fecha', ascending=False), use_container_width=True)
        else:
            st.dataframe(df.sort_values('fecha', ascending=False), use_container_width=True)

    elif menu == "📅 Citas de Hoy":
        hoy_f = datetime.now().date()
        df_hoy = df[df['fecha'].dt.date == hoy_f]
        st.write(f"Citas del día: {hoy_f.strftime('%d/%m/%Y')}")
        if not df_hoy.empty:
            st.dataframe(df_hoy, use_container_width=True)
        else:
            st.info("No hay servicios registrados para la fecha de hoy.")
