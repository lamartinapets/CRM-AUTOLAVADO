import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="CRM Pro - La Martina", layout="wide", page_icon="🐾")

# --- LOGIN SEGURO ---
if "auth" not in st.session_state:
    st.title("🔐 Acceso Administrativo - La Martina")
    col_l1, col_l2 = st.columns(2) # Corregido: número de columnas especificado
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
    # Carga desde la URL definida en Secrets
    df = conn.read(spreadsheet=st.secrets["connections"]["gsheets"]["spreadsheet"], worksheet="visitas")
    
    # Asegurar que existan columnas para hora y asistencia (aunque no estén en el Excel original)
    for col in ["hora", "asistencia"]:
        if col not in df.columns:
            df[col] = "Pendiente"
            
    # Convertir fecha al formato correcto (Columna C en tu Excel)
    df['fecha'] = pd.to_datetime(df['fecha'], dayfirst=True, errors='coerce')
    
    # Limpiar columna valor (Columna F)
    if 'valor' in df.columns:
        df['valor'] = df['valor'].astype(str).replace(r'[\$,]', '', regex=True)
        df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
        
    return df

df = load_data()

# --- INTERFAZ PRINCIPAL ---
st.title("🐾 CRM Estratégico La Martina")

menu = ["📅 Agenda y Asistencia", "📊 Tablero de Análisis", "🚨 Alerta de Retención", "🔍 Buscador Total"]
choice = st.sidebar.selectbox("Panel de Control", menu)

if choice == "📅 Agenda y Asistencia":
    st.subheader("📝 Gestión de Citas")
    t1, t2 = st.tabs(["🆕 Nueva Cita", "✅ Confirmar Asistencia"])
    
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
            valor = st.number_input("Valor del servicio", min_value=0)
            
            if st.form_submit_button("Guardar en Excel"):
                new_row = pd.DataFrame([{
                    "mascota": mascota, "raza": raza, "fecha": fecha.strftime('%d/%m/%Y'),
                    "cliente": cliente, "id": id_tel, "valor": valor, "Canal": canal,
                    "hora": hora.strftime('%H:%M'), "asistencia": "Pendiente"
                }])
                updated = pd.concat([df, new_row], ignore_index=True)
                conn.update(spreadsheet=st.secrets["connections"]["gsheets"]["spreadsheet"], data=updated, worksheet="visitas")
                st.success("✅ ¡Cita guardada!")
                st.cache_data.clear()
                st.rerun()

    with t2:
        st.write("### Citas para hoy")
        hoy = datetime.now().strftime('%Y-%m-%d')
        filtro_hoy = df[(df['fecha'].dt.strftime('%Y-%m-%d') == hoy) & (df['asistencia'] == "Pendiente")]
        
        if not filtro_hoy.empty:
            for idx, row in filtro_hoy.iterrows():
                col_a, col_b, col_c = st.columns()
                col_a.write(f"🐶 {row['mascota']} ({row['cliente']}) - {row['hora']}")
                if col_b.button("✅ Asistió", key=f"si_{idx}"):
                    df.at[idx, 'asistencia'] = "SÍ"
                    conn.update(spreadsheet=st.secrets["connections"]["gsheets"]["spreadsheet"], data=df, worksheet="visitas")
                    st.cache_data.clear()
                    st.rerun()
                if col_c.button("❌ No", key=f"no_{idx}"):
                    df.at[idx, 'asistencia'] = "NO"
                    conn.update(spreadsheet=st.secrets["connections"]["gsheets"]["spreadsheet"], data=df, worksheet="visitas")
                    st.cache_data.clear()
                    st.rerun()
        else:
            st.info("No hay citas pendientes para hoy.")

elif choice == "📊 Tablero de Análisis":
    st.subheader("💡 Análisis de Comportamiento")
    df_si = df[df['asistencia'] == "SÍ"]
    
    m1, m2 = st.columns(2)
    m1.metric("Ventas Totales", f"${df_si['valor'].sum():,.0f}")
    m2.metric("Clientes Atendidos", len(df_si))
    
    st.write("### Efectividad por Canal")
    st.bar_chart(df_si['Canal'].value_counts())

elif choice == "🚨 Alerta de Retención":
    st.subheader("Clientes que no han vuelto en 30 días")
    limite = datetime.now() - timedelta(days=30)
    # Buscar última visita exitosa por cliente
    fugas = df[df['asistencia'] == "SÍ"].groupby(['cliente', 'id'])['fecha'].max().reset_index()
    alerta = fugas[fugas['fecha'] < limite]
    st.table(alerta)

else:
    st.dataframe(df.sort_values('fecha', ascending=False), use_container_width=True)
