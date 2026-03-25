import streamlit as st
import pandas as pd
import re

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="CRM La Martina Pets", layout="wide", page_icon="🐾")

# --- LOGIN ---
if "authenticated" not in st.session_state:
    st.title("🔐 Acceso Administrativo")
    password = st.text_input("Contraseña del sistema", type="password")
    if st.button("Ingresar"):
        if password == st.secrets["password"]:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Contraseña incorrecta")
    st.stop()

# --- CARGA DE DATOS ROBUSTA ---
@st.cache_data(ttl=300)
def get_google_sheet_data():
    try:
        # Recuperamos el secreto sin importar su tipo
        raw_input = st.secrets["connections"]["gsheets"]["spreadsheet"]
        
        # Lógica Senior: Normalizar entrada (si es lista, tomar el primer elemento)
        if isinstance(raw_input, list):
            url_text = str(raw_input)
        else:
            url_text = str(raw_input)
            
        # Limpieza extrema de caracteres invisibles y espacios
        url_cleaned = url_text.strip().replace('"', '').replace("'", "")
        
        # Extraer ID del documento usando expresiones regulares (más seguro que .split)
        match = re.search(r"/d/([a-zA-Z0-9-_]+)", url_cleaned)
        if match:
            doc_id = match.group(1)
            final_csv_url = f"https://docs.google.com/spreadsheets/d/{doc_id}/export?format=csv"
        else:
            # Si no hay ID, intentamos usar la URL tal cual
            final_csv_url = url_cleaned
            
        return pd.read_csv(final_csv_url)
    except Exception as e:
        st.error(f"Error crítico de conexión: {str(e)}")
        return None

# --- INTERFAZ PRINCIPAL ---
st.title("🐾 CRM La Martina Pets")
st.markdown("---")

data = get_google_sheet_data()

if data is not None:
    # Buscador Senior
    search_term = st.text_input("🔍 Buscador inteligente (Nombre, Mascota, Teléfono...)", placeholder="Escribe aquí para filtrar...")
    
    if search_term:
        # Filtro de texto completo en el dataframe
        filtered_df = data[data.apply(lambda row: row.astype(str).str.contains(search_term, case=False).any(), axis=1)]
        st.success(f"Se encontraron {len(filtered_df)} registros.")
        st.dataframe(filtered_df, use_container_width=True, hide_index=True)
    else:
        st.dataframe(data, use_container_width=True, hide_index=True)
else:
    st.warning("No se pudo cargar la base de datos. Verifique que el enlace en Secrets sea correcto y que el archivo de Google Sheets tenga activada la opción 'Cualquier persona con el enlace puede leer'.")
