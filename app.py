import streamlit as st
import pandas as pd

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="CRM La Martina Pets", layout="centered", page_icon="🐾")

# --- LOGIN SEGURO (Versión simplificada sin columnas para evitar errores) ---
def check_password():
    if "password_correct" not in st.session_state:
        st.title("🔐 Acceso Restringido")
        st.subheader("La Martina Pets - CRM")
        
        # Formulario de login
        password = st.text_input("Introduce la contraseña", type="password")
        
        if st.button("Entrar"):
            # Compara con la contraseña de tus Secrets
            if password == st.secrets["password"]:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("❌ Contraseña incorrecta")
        return False
    return True

# Si no ha pasado el login, detiene la ejecución aquí
if not check_password():
    st.stop()

# --- CONEXIÓN A DATOS (Método Directo) ---
@st.cache_data(ttl=600)
def load_data():
    try:
        # URL desde Secrets
        sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        
        # Limpiamos la URL para forzar la descarga de datos
        if "/edit" in sheet_url:
            csv_url = sheet_url.split("/edit") + "/export?format=csv"
        else:
            csv_url = sheet_url
            
        return pd.read_csv(csv_url)
    except Exception as e:
        st.error(f"Error al conectar con los datos: {e}")
        return None

# --- CUERPO DE LA APP ---
st.title("🐾 CRM La Martina Pets")
st.write("Bienvenido al sistema de gestión.")

df = load_data()

if df is not None:
    st.success("✅ Conexión establecida con la base de datos")
    
    # Buscador de clientes
    busqueda = st.text_input("🔍 Buscar cliente (Nombre, Mascota o Teléfono)")
    
    if busqueda:
        # Filtra en todo el documento
        mask = df.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)
        df_mostrar = df[mask]
    else:
        df_mostrar = df
        
    # Mostrar tabla
    st.dataframe(df_mostrar, use_container_width=True)
else:
    st.warning("⚠️ No se pudieron cargar los datos. Revisa los permisos del Excel.")

# Comentario de actualización forzada: v2.0
