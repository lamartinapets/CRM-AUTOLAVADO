import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="CRM La Martina Pets", layout="wide", page_icon="🐾")

# --- LOGIN ---
if "auth" not in st.session_state:
    st.title("🔐 Acceso La Martina")
    pw = st.text_input("Ingrese la clave", type="password")
    if st.button("Ingresar"):
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
        df['fecha'] = pd.to_datetime(df['fecha'], dayfirst=True, errors='coerce')
        
        if 'valor' in df.columns:
            df['valor'] = df['valor'].astype(str).replace(r'[\$,\.]', '', regex=True)
            df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
            
        if 'Canal' in df.columns:
            df['Canal'] = df['Canal'].str.strip().str.capitalize().replace({'Tiktok': 'TikTok'})
            
        return df
    except:
        return None

df = load_data()

# --- INTERFAZ ---
st.title("🐾 CRM La Martina Pets")

if df is not None:
    menu = st.sidebar.radio("Navegación", ["📈 Dashboard Salud", "🔍 Buscador e Historial", "📅 Citas de Hoy"])

    if menu == "📈 Dashboard Salud":
        st.subheader("Estado de la Cartera de Clientes")
        
        # --- LÓGICA DE CLASIFICACIÓN (AJUSTADA A 30 DÍAS) ---
        hoy = datetime.now()
        # Buscamos la fecha de la última visita por mascota
        ultimo_contacto = df.groupby('mascota')['fecha'].max().reset_index()
        
        def clasificar(fecha):
            if pd.isna(fecha): return "Sin datos"
            dias = (hoy - fecha).days
            if dias <= 30: return "Activo (Fiel)"
            if dias <= 60: return "Medio (En riesgo)"
            return "Perdido (Inactivo)"

        ultimo_contacto['Estado'] = ultimo_contacto['fecha'].apply(clasificar)
        
        # Ordenamos las categorías para que la gráfica se vea lógica
        orden_salud = ["Activo (Fiel)", "Medio (En riesgo)", "Perdido (Inactivo)"]
        resumen_salud = ultimo_contacto['Estado'].value_counts().reindex(orden_salud).fillna(0)

        # KPIs Principales
        k1, k2, k3 = st.columns(3)
        k1.metric("Ventas Totales", f"${df['valor'].sum():,.0f}")
        k2.metric("Servicios Realizados", len(df))
        k3.metric("Mascotas Únicas", len(ultimo_contacto))

        st.divider()

        # Gráfico de Salud
        c1, c2 = st.columns()
        with c1:
            st.write("#### Clasificación de Mascotas")
            st.bar_chart(resumen_salud)
        with c2:
            st.write("#### Conteo Real")
            st.write(resumen_salud)

        st.divider()
        st.write("### 🚨 Clientes para recuperación (Perdidos)")
        st.info("Estos clientes no han vuelto en más de 60 días. ¡Es momento de enviarles una promo!")
        
        perdidos = ultimo_contacto[ultimo_contacto['Estado'] == "Perdido (Inactivo)"]
        # Traemos datos de contacto del dataframe original
        info_perdidos = pd.merge(perdidos, df[['mascota', 'cliente', 'id']], on='mascota', how='left').drop_duplicates('mascota')
        st.dataframe(info_perdidos[['mascota', 'cliente', 'id', 'fecha']], use_container_width=True)

    elif menu == "🔍 Buscador e Historial":
        st.subheader("Historial de Visitas")
        busqueda = st.text_input("Buscar por nombre de mascota o dueño")
        if busqueda:
            res = df[df.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)]
            st.dataframe(res.sort_values('fecha', ascending=False), use_container_width=True)
        else:
            st.dataframe(df.sort_values('fecha', ascending=False), use_container_width=True)

    elif menu == "📅 Citas de Hoy":
        hoy_fecha = datetime.now().date()
        df_hoy = df[df['fecha'].dt.date == hoy_fecha]
        st.write(f"Agenda para hoy: {hoy_fecha.strftime('%d/%m/%Y')}")
        if not df_hoy.empty:
            st.dataframe(df_hoy[['mascota', 'cliente', 'id', 'Canal']], use_container_width=True)
        else:
            st.info("No hay citas registradas para hoy.")
