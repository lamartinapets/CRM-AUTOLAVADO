import streamlit as st
import pandas as pd
from st_gsheets_connection import GSheetsConnection
import re
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="CRM La Martina PRO", layout="wide")

# --- SISTEMA DE SEGURIDAD (LOGIN) ---
def check_password():
    if "password_correct" not in st.session_state:
        st.title("🔐 Acceso Restringido - La Martina")
        st.write("Bienvenido. Por favor, introduce la clave para gestionar los datos.")
        password = st.text_input("Contraseña", type="password")
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

# --- MENÚ PRINCIPAL ---
st.sidebar.title("🐾 La Martina Pets")
menu = st.sidebar.radio("Menú", ["📅 Agenda", "🗂️ CRM", "📊 Dashboard"])

# =========================================================
# 📅 AGENDA
# =========================================================
if menu == "📅 Agenda":
    st.title("📅 Gestión de Agenda")
    df_visitas = leer_datos("visitas")
    df_clientes = leer_datos("clientes")
    df_mascotas = leer_datos("mascotas")

    with st.expander("➕ Crear Nueva Cita"):
        tipo = st.radio("Cliente", ["Existente", "Nuevo"], horizontal=True)
        if tipo == "Existente" and not df_clientes.empty:
            busq = st.text_input("Buscar cliente")
            filtro = df_clientes[df_clientes["propietario"].str.contains(busq, case=False, na=False)]
            if not filtro.empty:
                opciones = filtro["propietario"] + " (" + filtro["id"].astype(str) + ")"
                c_sel = st.selectbox("Selecciona", opciones)
                id_final = c_sel.split("(")[-1].replace(")", "")
                m_list = df_mascotas[df_mascotas["id"].astype(str) == id_final]["nombre"].tolist()
                mascota_sel = st.selectbox("Mascota", ["Nueva"] + m_list)
                mascota_final = st.text_input("Nombre mascota") if mascota_sel == "Nueva" else mascota_sel
            else: id_final = None
        else:
            id_final = st.text_input("Teléfono (ID)")
            nombre_p = st.text_input("Nombre Propietario")
            mascota_final = st.text_input("Mascota")
        
        f_cita = st.date_input("Fecha", datetime.now())
        v_cita = st.number_input("Valor", value=0)

        if st.button("✅ Guardar Cita") and id_final:
            nueva = pd.DataFrame([{"id": id_final, "mascota": mascota_final, "fecha": f_cita.strftime("%d/%m/%Y"), "valor": v_cita, "estado": "Agendado"}])
            if tipo == "Nuevo":
                nc = pd.DataFrame([{"id": id_final, "propietario": nombre_p}])
                guardar_datos(pd.concat([df_clientes, nc]), "clientes")
            guardar_datos(pd.concat([df_visitas, nueva]), "visitas")
            st.success("¡Cita guardada!")
            st.rerun()

    st.divider()
    st.subheader("📋 Citas Programadas")
    st.dataframe(df_visitas, use_container_width=True)

# =========================================================
# 🗂️ CRM
# =========================================================
elif menu == "🗂️ CRM":
    st.title("🗂️ Base de Datos")
    st.dataframe(leer_datos("clientes"), use_container_width=True)

# =========================================================
# 📊 DASHBOARD
# =========================================================
elif menu == "📊 Dashboard":
    st.title("📊 Análisis")
    v = leer_datos("visitas")
    if not v.empty:
        st.metric("Ventas Totales", f"${v['valor'].sum():,.0f}")
        st.bar_chart(v.groupby("fecha")["valor"].sum())
