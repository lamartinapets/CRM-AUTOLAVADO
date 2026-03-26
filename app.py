import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="CRM La Martina Pets", layout="wide")

# --- LOGIN ---
if "auth" not in st.session_state:
    st.title("🔐 Acceso Administrativo")
    pw = st.text_input("Contraseña", type="password")
    if st.button("Entrar"):
        if pw == st.secrets["password"]:
            st.session_state["auth"] = True
            st.rerun()
        else:
            st.error("Contraseña incorrecta")
    st.stop()

# --- CONEXIÓN DE LECTURA (Plan B Seguro) ---
# Usamos el ID de tu hoja compartido públicamente para evitar errores de llave privada
SHEET_ID = "1rHtwtskyxyY2mp32sCQ4VRiQ5pLOZpM4jiBs9vbYtmw"
# Leemos la pestaña 'visitas' que aparece en tu imagen 6
url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=visitas"

@st.cache_data(ttl=0)
def load_data():
    # Cargamos datos directamente
    df = pd.read_csv(url)
    # Limpiamos nombres de columnas por si tienen espacios ocultos
    df.columns = df.columns.str.strip()
    # Convertimos la fecha (Columna C)
    df['fecha'] = pd.to_datetime(df['fecha'], dayfirst=True, errors='coerce')
    # Limpiamos el valor (Columna F) quitando el símbolo $
    if 'valor' in df.columns:
        df['valor'] = df['valor'].astype(str).replace(r'[\$,]', '', regex=True).astype(float)
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"Error de conexión: {e}")
    st.info("Asegúrate de que el Excel siga compartido como 'Cualquier persona con el enlace'.")
    st.stop()

# --- INTERFAZ ---
st.title("🐾 CRM La Martina Pets")

menu = st.sidebar.selectbox("Menú", ["📊 Dashboard", "📅 Citas de Hoy", "🔍 Buscador General"])

if menu == "📊 Dashboard":
    st.subheader("Análisis de Negocio")
    col1, col2 = st.columns(2)
    with col1:
        st.write("#### Efectividad por Canal")
        if 'Canal' in df.columns:
            st.bar_chart(df['Canal'].value_counts())
    with col2:
        st.write("#### Mascotas por Raza")
        if 'raza' in df.columns:
            st.bar_chart(df['raza'].value_counts().head(5))
    
    st.divider()
    st.metric("Ventas Totales Registradas", f"${df['valor'].sum():,.0f}")

elif menu == "📅 Citas de Hoy":
    st.subheader("Agenda del Día")
    hoy = datetime.now().strftime('%Y-%m-%d')
    # Filtramos por la fecha de hoy
    df_hoy = df[df['fecha'].dt.strftime('%Y-%m-%d') == hoy]
    
    if not df_hoy.empty:
        st.table(df_hoy[['mascota', 'cliente', 'id', 'Canal']])
    else:
        st.info("No hay citas registradas con la fecha de hoy.")

else:
    st.subheader("Buscador de Clientes")
    search = st.text_input("Buscar por nombre de mascota o cliente")
    if search:
        # Filtro inteligente en toda la tabla
        mask = df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)
        st.dataframe(df[mask], use_container_width=True)
    else:
        st.dataframe(df, use_container_width=True)
