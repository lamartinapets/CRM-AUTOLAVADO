import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="CRM La Martina Pets", layout="wide", page_icon="🐾")

# --- LOGIN ---
if "auth" not in st.session_state:
    st.title("🔐 Acceso Administrativo")
    pw = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        if pw == st.secrets["password"]:
            st.session_state["auth"] = True
            st.rerun()
    st.stop()

# --- CONEXIÓN ---
SHEET_ID = "1rHtwtkyxsyY2mp32sCQ4VRiQ5pLOZpM4jiBs9vbYtmw"
URL_VISITAS = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"
URL_AGENDA = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=agenda"

@st.cache_data(ttl=5)
def load_data():
    try:
        # 1. Cargar Historial (Hoja Visitas)
        df_v = pd.read_csv(URL_VISITAS)
        df_v.columns = [c.strip() for c in df_v.columns]
        df_v['fecha'] = pd.to_datetime(df_v['fecha'], dayfirst=True, errors='coerce')
        if 'valor' in df_v.columns:
            df_v['valor'] = pd.to_numeric(df_v['valor'].astype(str).replace(r'[\$,\.]', '', regex=True), errors='coerce').fillna(0)
        
        # 2. Cargar Agenda
        df_a = pd.read_csv(URL_AGENDA)
        df_a.columns = [c.strip() for c in df_a.columns]
        
        # Flexibilidad en Fecha y Hora
        df_a['fecha'] = pd.to_datetime(df_a['fecha'], dayfirst=True, errors='coerce')
        if 'hora' in df_a.columns:
            df_a['hora'] = df_a['hora'].fillna("--:--").astype(str)
        
        # Limpiar Abonos y Totales
        for col in ['abono', 'valor total']:
            if col in df_a.columns:
                df_a[col] = pd.to_numeric(df_a[col].astype(str).replace(r'[\$,\.]', '', regex=True), errors='coerce').fillna(0)
        
        # Ordenar Agenda
        if not df_a.empty:
            df_a = df_a.sort_values(by=['fecha', 'hora'], ascending=[True, True])
            
        return df_v, df_a
    except Exception as e:
        st.error(f"Error de lectura: {e}")
        return None, None

df_visitas, df_agenda = load_data()

# --- INTERFAZ ---
if df_visitas is not None:
    st.title("🐾 CRM La Martina Pets")
    
    menu = st.sidebar.radio("Navegación", ["📅 Agenda y Abonos", "📈 Dashboard Salud", "🔍 Buscador Global"])

    if menu == "📅 Agenda y Abonos":
        st.subheader("📅 Control de Citas y Saldos Pendientes")
        
        if df_agenda is not None and not df_agenda.empty:
            agenda_calc = df_agenda.copy()
            if 'valor total' in agenda_calc.columns and 'abono' in agenda_calc.columns:
                agenda_calc['Saldo Pendiente'] = agenda_calc['valor total'] - agenda_calc['abono']
            
            # Mostrar Tabla con Estilo
            cols_show = ['fecha', 'hora', 'mascota', 'cliente', 'servicio', 'valor total', 'abono', 'Saldo Pendiente']
            actual = [c for c in cols_show if c in agenda_calc.columns]
            
            st.dataframe(agenda_calc[actual].style.format({
                'valor total': '${:,.0f}', 'abono': '${:,.0f}', 'Saldo Pendiente': '${:,.0f}'
            }).applymap(lambda x: 'background-color: #ffcccc' if isinstance(x, (int, float)) and x > 0 else '', subset=['Saldo Pendiente']), 
            use_container_width=True)
            
            # Resumen de Cobro Diario
            hoy_f = datetime.now().date()
            saldo_hoy = agenda_calc[agenda_calc['fecha'].dt.date == hoy_f]['Saldo Pendiente'].sum()
            st.metric("Total por cobrar hoy", f"${saldo_hoy:,.0f}")
        else:
            st.info("No hay datos en la pestaña 'agenda'.")
        
        st.divider()
        st.link_button("📝 Abrir Excel", f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit")

    elif menu == "📈 Dashboard Salud":
        st.subheader("Estado de Clientes (Base: 30 días)")
        hoy = datetime.now()
        ultimo = df_visitas.sort_values('fecha').groupby('mascota').tail(1).copy()
        
        def clasificar(fecha):
            if pd.isna(fecha): return "Sin datos"
            dias = (hoy - fecha).days
            if dias <= 30: return "Activo"
            if dias <= 60: return "Medio"
            return "Perdido"

        ultimo['Estado'] = ultimo['fecha'].apply(clasificar)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Ingresos", f"${df_visitas['valor'].sum():,.0f}")
        c2.metric("Servicios", len(df_visitas))
        c3.metric("Mascotas", len(ultimo))
        
        st.bar_chart(ultimo['Estado'].value_counts())
        
        t1, t2, t3 = st.tabs(["✅ Activos", "⚠️ Medios", "🚨 Perdidos"])
        with t1: st.dataframe(ultimo[ultimo['Estado']=="Activo"], use_container_width=True)
        with t2: st.dataframe(ultimo[ultimo['Estado']=="Medio"], use_container_width=True)
        with t3: st.dataframe(ultimo[ultimo['Estado']=="Perdido"], use_container_width=True)

    elif menu == "🔍 Buscador Global":
        st.subheader("Historial Completo")
        busq = st.text_input("Buscar mascota o dueño")
        if busq:
            res = df_visitas[df_visitas.astype(str).apply(lambda x: x.str.contains(busq, case=False)).any(axis=1)]
            st.dataframe(res.sort_values('fecha', ascending=False), use_container_width=True)
