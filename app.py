import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="CRM Pro - La Martina", layout="wide", page_icon="🐾")

# --- LOGIN SEGURO ---
if "auth" not in st.session_state:
    st.title("🔐 Acceso Administrativo - La Martina")
    # CORRECCIÓN: Se define el número de columnas para evitar el TypeError
    col_l1, col_l2 = st.columns(2) 
    with col_l1:
        pw = st.text_input("Ingrese la contraseña de seguridad", type="password")
    if st.button("Ingresar"):
        if pw == st.secrets["password"]:
            st.session_state["auth"] = True
            st.rerun()
        else:
            st.error("❌ Contraseña incorrecta.")
    st.stop()

# --- CONEXIÓN ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=0)
def load_data():
    df = conn.read(spreadsheet=st.secrets["connections"]["gsheets"]["spreadsheet"], worksheet="visitas")
    
    # Asegurar columnas necesarias
    for col in ["hora", "asistencia"]:
        if col not in df.columns:
            df[col] = "Pendiente"
            
    df['fecha'] = pd.to_datetime(df['fecha'], dayfirst=True, errors='coerce')
    
    if 'valor' in df.columns:
        df['valor'] = df['valor'].astype(str).replace(r'[\$,]', '', regex=True)
        df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
        
    return df

df = load_data()

# --- INTERFAZ ---
st.title("🐾 CRM La Martina Pets")

menu = ["📅 Agenda & Asistencia", "📊 Análisis", "🚨 Alertas", "🔍 Buscador"]
choice = st.sidebar.selectbox("Menú", menu)

if choice == "📅 Agenda & Asistencia":
    st.subheader("📝 Gestión de Citas")
    t1, t2 = st.tabs(["🆕 Nueva Cita", "✅ Confirmar"])
    
    with t1:
        with st.form("registro", clear_on_submit=True):
            c1, c2 = st.columns(2)
            mascota = c1.text_input("Mascota")
            raza = c1.text_input("Raza")
            cliente = c2.text_input("Dueño")
            id_tel = c2.text_input("Teléfono (ID)")
            
            f1, f2, f3 = st.columns(3)
            fecha = f1.date_input("Fecha")
            hora = f2.time_input("Hora")
            canal = f3.selectbox("Canal", ["Local", "WhatsApp", "Instagram", "Pauta ads", "Volante"])
            valor = st.number_input("Valor", min_value=0)
            
            if st.form_submit_button("Guardar"):
                new_row = pd.DataFrame([{
                    "mascota": mascota, "raza": raza, "fecha": fecha.strftime('%d/%m/%Y'),
                    "cliente": cliente, "id": id_tel, "valor": valor, "Canal": canal,
                    "hora": hora.strftime('%H:%M'), "asistencia": "Pendiente"
                }])
                updated = pd.concat([df, new_row], ignore_index=True)
                conn.update(spreadsheet=st.secrets["connections"]["gsheets"]["spreadsheet"], data=updated, worksheet="visitas")
                st.success("✅ Guardado en Excel")
                st.cache_data.clear()
                st.rerun()

    with t2:
        hoy = datetime.now().strftime('%Y-%m-%d')
        pendientes = df[(df['fecha'].dt.strftime('%Y-%m-%d') == hoy) & (df['asistencia'] == "Pendiente")]
        if not pendientes.empty:
            for idx, row in pendientes.iterrows():
                col_a, col_b = st.columns()
                col_a.write(f"🐶 {row['mascota']} - {row['hora']}")
                if col_b.button("Asistió", key=idx):
                    df.at[idx, 'asistencia'] = "SÍ"
                    conn.update(spreadsheet=st.secrets["connections"]["gsheets"]["spreadsheet"], data=df, worksheet="visitas")
                    st.cache_data.clear()
                    st.rerun()
        else:
            st.info("No hay citas para hoy.")

elif choice == "📊 Análisis":
    st.metric("Ventas Totales", f"${df[df['asistencia'] == 'SÍ']['valor'].sum():,.0f}")
    st.bar_chart(df['Canal'].value_counts())

elif choice == "🚨 Alertas":
    limite = datetime.now() - timedelta(days=30)
    st.table(df[df['fecha'] < limite][['cliente', 'id', 'fecha']])

else:
    st.dataframe(df.sort_values('fecha', ascending=False))
