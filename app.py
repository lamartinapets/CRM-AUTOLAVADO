import streamlit as st
import pandas as pd
import re
import os
from datetime import datetime

# --- TRUCO DE COMPATIBILIDAD (Para evitar el error ModuleNotFoundError) ---
try:
    from st_gsheets_connection import GSheetsConnection
except ModuleNotFoundError:
    os.system("pip install st-gsheets-connection")
    from st_gsheets_connection import GSheetsConnection

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="CRM La Martina Pets", layout="wide", page_icon="🐾")

# --- SISTEMA DE SEGURIDAD (LOGIN) ---
def check_password():
    """Devuelve True si el usuario introdujo la contraseña correcta."""
    if "password_correct" not in st.session_state:
        st.markdown("<br><br>", unsafe_allow_index=True)
        col1, col2, col3 = st.columns()
        with col2:
            st.title("🔐 Acceso Restringido")
            st.subheader("La Martina Pets - CRM")
            password = st.text_input("Introduce la contraseña para entrar", type="password")
            if st.button("Entrar"):
                if password == st.secrets["password"]:
                    st.session_state["password_correct"] = True
                    st.rerun()
                else:
                    st.error("❌ Contraseña incorrecta")
        return False
    return True

if not check_password():
    st.stop()

# --- CONEXIÓN A GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def leer_datos(tabla):
    return conn.read(worksheet=tabla, ttl="0")

def guardar_datos(df, tabla):
    conn.update(worksheet=tabla, data=df)
    st.cache_data.clear()

# --- MENÚ LATERAL ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/194/194279.png", width=100)
st.sidebar.title("La Martina Pets")
menu = st.sidebar.radio("Navegación", ["📅 Agenda de Citas", "🗂️ Base de Clientes", "📊 Reportes"])

# =========================================================
# 📅 AGENDA DE CITAS
# =========================================================
if menu == "📅 Agenda de Citas":
    st.title("📅 Gestión de Citas")
    
    # Cargar datos
    df_visitas = leer_datos("visitas")
    df_clientes = leer_datos("clientes")

    with st.expander("➕ Agendar Nueva Visita"):
        col1, col2 = st.columns(2)
        with col1:
            tipo_cliente = st.radio("Tipo de Cliente", ["Existente", "Nuevo"], horizontal=True)
            
            if tipo_cliente == "Existente" and not df_clientes.empty:
                opciones = df_clientes["propietario"] + " (" + df_clientes["id"].astype(str) + ")"
                cliente_sel = st.selectbox("Selecciona el Cliente", opciones)
                id_final = cliente_sel.split("(")[-1].replace(")", "")
                nombre_p = cliente_sel.split(" (")
            else:
                id_final = st.text_input("Teléfono / ID")
                nombre_p = st.text_input("Nombre del Propietario")

        with col2:
            mascota = st.text_input("Nombre de la Mascota")
            fecha = st.date_input("Fecha de la Cita", datetime.now())
            valor = st.number_input("Valor del Servicio", min_value=0, step=5000)

        if st.button("✅ Registrar Cita"):
            if id_final and mascota:
                # Nueva fila para visitas
                nueva_visita = pd.DataFrame([{
                    "id": id_final,
                    "mascota": mascota,
                    "fecha": fecha.strftime("%d/%m/%Y"),
                    "valor": valor,
                    "estado": "Completado"
                }])
                
                # Si es nuevo, agregarlo a clientes
                if tipo_cliente == "Nuevo":
                    nuevo_cliente = pd.DataFrame([{"id": id_final, "propietario": nombre_p}])
                    df_clientes = pd.concat([df_clientes, nuevo_cliente], ignore_index=True)
                    guardar_datos(df_clientes, "clientes")
                
                # Guardar visita
                df_visitas = pd.concat([df_visitas, nueva_visita], ignore_index=True)
                guardar_datos(df_visitas, "visitas")
                st.success(f"¡Cita de {mascota} registrada con éxito!")
                st.rerun()
            else:
                st.warning("Por favor completa los campos obligatorios.")

    st.divider()
    st.subheader("📋 Historial Reciente")
    st.dataframe(df_visitas.tail(10), use_container_width=True)

# =========================================================
# 🗂️ BASE DE CLIENTES
# =========================================================
elif menu == "🗂️ Base de Clientes":
    st.title("🗂️ Base de Datos de Clientes")
    df_c = leer_datos("clientes")
    
    busqueda = st.text_input("🔍 Buscar por nombre o teléfono")
    if busqueda:
        df_c = df_c[df_c.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)]
    
    st.dataframe(df_c, use_container_width=True)

# =========================================================
# 📊 REPORTES
# =========================================================
elif menu == "📊 Reportes":
    st.title("📊 Resumen de Ingresos")
    df_v = leer_datos("visitas")
    
    if not df_v.empty:
        total = df_v["valor"].sum()
        servicios = len(df_v)
        
        c1, c2 = st.columns(2)
        c1.metric("Ingresos Totales", f"${total:,.0f}")
        c2.metric("Total Servicios", servicios)
        
        st.subheader("Ingresos por Fecha")
        chart_data = df_v.groupby("fecha")["valor"].sum()
        st.bar_chart(chart_data)
    else:
        st.info("Aún no hay datos para mostrar reportes.")
