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
        # 1. CARGAR HISTORIAL (VISITAS)
        df_v = pd.read_csv(URL_VISITAS)
        df_v.columns = [c.strip() for c in df_v.columns]
        df_v['fecha'] = pd.to_datetime(df_v['fecha'], dayfirst=True, errors='coerce')
        
        if 'valor' in df_v.columns:
            df_v['valor'] = df_v['valor'].astype(str).str.replace(r'[^\d]', '', regex=True)
            df_v['valor'] = pd.to_numeric(df_v['valor'], errors='coerce').fillna(0).astype(int)
            df_v['valor'] = df_v['valor'].apply(lambda x: x/100 if x > 1000000 else x)
        
        # 2. CARGAR AGENDA
        df_a = pd.read_csv(URL_AGENDA)
        df_a.columns = [c.strip() for c in df_a.columns]
        df_a['fecha'] = pd.to_datetime(df_a['fecha'], dayfirst=True, errors='coerce')
        
        # Limpieza de números
        for col in ['abono', 'valor total']:
            if col in df_a.columns:
                df_a[col] = df_a[col].astype(str).str.replace(r'[^\d]', '', regex=True)
                df_a[col] = pd.to_numeric(df_a[col], errors='coerce').fillna(0).astype(int)
                df_a[col] = df_a[col].apply(lambda x: x/100 if x > 1000000 else x)
        
        # ORDENAR MENOR A MAYOR (Fecha y luego Hora)
        if not df_a.empty:
            # Aseguramos que la hora tenga formato HH:MM para ordenar bien
            df_a['hora'] = df_a['hora'].fillna("00:00").astype(str)
            df_a = df_a.sort_values(by=['fecha', 'hora'], ascending=[True, True])
            
        return df_v, df_a
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
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
            
            # --- NUEVA LÓGICA: DÍA DE LA SEMANA ---
            dias_dict = {
                'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
                'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
            }
            agenda_calc['Día'] = agenda_calc['fecha'].dt.day_name().map(dias_dict)
            agenda_calc['Fecha'] = agenda_calc['fecha'].dt.strftime('%d/%m/%Y')
            
            # Cálculo de Saldo
            agenda_calc['Saldo Pendiente'] = agenda_calc['valor total'] - agenda_calc['abono']
            
            # Columnas a mostrar (incluyendo el Día)
            cols_ver = ['Día', 'Fecha', 'hora', 'mascota', 'cliente', 'servicio', 'valor total', 'abono', 'Saldo Pendiente']
            
            st.dataframe(agenda_calc[cols_ver].style.format({
                'valor total': '${:,.0f}', 'abono': '${:,.0f}', 'Saldo Pendiente': '${:,.0f}'
            }).applymap(lambda x: 'background-color: #ffcccc' if isinstance(x, (int, float)) and x > 0 else '', subset=['Saldo Pendiente']), 
            use_container_width=True)
            
            # Resumen de cobros hoy
            hoy_actual = datetime.now().date()
            saldo_hoy = agenda_calc[agenda_calc['fecha'].dt.date == hoy_actual]['Saldo Pendiente'].sum()
            st.metric(f"Cobros pendientes para hoy", f"${saldo_hoy:,.0f}")
            
        else:
            st.info("No hay citas registradas.")

    elif menu == "📈 Dashboard Salud":
        st.subheader("Estado de Clientes")
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
        c1.metric("Ingresos Históricos", f"${df_visitas['valor'].sum():,.0f}")
        c2.metric("Servicios Realizados", len(df_visitas))
        k_mascotas = len(ultimo)
        c3.metric("Mascotas Únicas", k_mascotas)
        
        st.bar_chart(ultimo['Estado'].value_counts())
        
        t1, t2, t3 = st.tabs(["✅ Activos", "⚠️ Medios", "🚨 Perdidos"])
        with t1: st.dataframe(ultimo[ultimo['Estado']=="Activo"], use_container_width=True)
        with t2: st.dataframe(ultimo[ultimo['Estado']=="Medio"], use_container_width=True)
        with t3: st.dataframe(ultimo[ultimo['Estado']=="Perdido"], use_container_width=True)

    elif menu == "🔍 Buscador Global":
        st.subheader("Historial de Mascotas")
        busq = st.text_input("Buscar por mascota o dueño")
        if busq:
            res = df_visitas[df_visitas.astype(str).apply(lambda x: x.str.contains(busq, case=False)).any(axis=1)]
            st.dataframe(res.sort_values('fecha', ascending=False), use_container_width=True)
