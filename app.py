import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="CRM Pro - La Martina", layout="wide", page_icon="🐾")

# --- LOGIN SEGURO ---
# Bloqueamos el acceso hasta que se introduzca la contraseña correcta
if "auth" not in st.session_state:
    st.title("🔐 Acceso Administrativo - La Martina")
    col_l1, col_l2 = st.columns()
    with col_l1:
        pw = st.text_input("Ingrese la contraseña de seguridad", type="password")
    if st.button("Ingresar"):
        if pw == st.secrets["password"]:
            st.session_state["auth"] = True
            st.rerun()
        else:
            st.error("❌ Contraseña incorrecta. Acceso denegado.")
    st.stop() # Detiene la ejecución aquí si no está logueado

# --- CONEXIÓN A GOOGLE SHEETS (Modo Seguro/Escritura) ---
try:
    # Usamos la conexión oficial st.connection
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"Error crítico de conexión: {e}")
    st.info("Verifique que los Secrets y permisos del bot sean correctos.")
    st.stop()

# --- FUNCIÓN PARA CARGAR Y LIMPIAR DATOS ---
@st.cache_data(ttl=0) # ttl=0 asegura datos frescos en cada refresco manual
def load_and_prepare_data():
    try:
        # Leemos la pestaña 'visitas' que es la que se muestra en tu imagen 9
        df = conn.read(
            spreadsheet=st.secrets["connections"]["gsheets"]["spreadsheet"],
            worksheet="visitas",
            ttl=0
        )
        
        # AJUSTE TÉCNICO: Aseguramos que existan las columnas solicitadas que no están en la imagen
        columnas_base = ["mascota", "raza", "fecha", "cliente", "id", "valor", "Canal"]
        columnas_extras = ["hora", "asistencia"]
        
        # Validamos que las columnas de la imagen existan (pueden faltar si el Excel está vacío)
        for col in columnas_base:
            if col not in df.columns:
                df[col] = ""
                
        # Añadimos las columnas nuevas (hora, asistencia) si no existen
        for col in columnas_extras:
            if col not in df.columns:
                df[col] = "Pendiente" # Estado inicial por defecto

        # Limpieza profunda de fechas (Columna C)
        df['fecha'] = pd.to_datetime(df['fecha'], dayfirst=True, errors='coerce')
        
        # Limpieza de valor (Columna F) para cálculos
        if 'valor' in df.columns:
            # Quitamos $ y , si existen en la tabla
            df['valor'] = df['valor'].astype(str).replace(r'[\$,]', '', regex=True)
            df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
            
        return df, "visitas"
    except Exception as e:
        st.error(f"Error leyendo la pestaña 'visitas': {e}")
        st.info("Asegúrese de que la pestaña en Excel se llame exactamente 'visitas' (todo en minúsculas).")
        st.stop()

# Obtenemos los datos limpios y el nombre de la hoja
df, sheet_name = load_and_prepare_data()

# --- INTERFAZ PRINCIPAL ---
st.title("🐾 CRM Estratégico La Martina")

# Menú lateral para las diferentes funciones solicitadas
with st.sidebar:
    st.write("---")
    st.write("### Panel de Control")
    # Menu profesional (Dashboard primero para la toma de decisiones)
    menu = ["📊 Tablero de Análisis", "📅 Agenda y Asistencia", "🚨 Alerta de Retención", "🔍 Buscador Total"]
    choice = st.selectbox("Seleccione Función", menu)
    st.write("---")
    if st.button("🔄 Refrescar Datos (TTL=0)"):
        st.cache_data.clear()
        st.rerun()
    st.write("---")

# --- 1. TABLERO DE ANÁLISIS (Para la toma de decisiones) ---
if choice == "📊 Tablero de Análisis":
    st.subheader("💡 Análisis del Comportamiento de Clientes")
    
    # Filtramos solo los que ASISTIERON ('SÍ') para las finanzas reales
    df_asistidos = df[df['asistencia'] == "SÍ"]
    
    # KPIs Principales
    k1, k2, k3 = st.columns(3)
    with k1:
        st.metric("💰 Ventas Efectivas", f"${df_asistidos['valor'].sum():,.0f}")
    with k2:
        st.metric("🐕 Total Mascotas Atendidas", len(df_asistidos))
    with k3:
        # Ticket promedio real
        if not df_asistidos.empty:
            ticket = df_asistidos['valor'].mean()
        else:
            ticket = 0
        st.metric("💳 Ticket Promedio Real", f"${ticket:,.0f}")

    st.divider()
    
    # Gráficos de Decisión
    g1, g2 = st.columns(2)
    
    with g1:
        st.write("### 📢 Efectividad por Canal")
        canal_data = df_asistidos['Canal'].value_counts()
        if not canal_data.empty:
            st.bar_chart(canal_data)
            st.caption("Decisión: Invierte más en el canal que trae más asistencia (SÍ).")
        else:
            st.info("Aún no hay datos de asistencia para analizar canales.")
            
    with g2:
        st.write("### 🐶 Razas más Rentables")
        if not df_asistidos.empty:
            raza_data = df_asistidos.groupby('raza')['valor'].sum().sort_values(ascending=False).head(5)
            st.bar_chart(raza_data)
            st.caption("Decisión: Crea promociones exclusivas para estas razas de alto valor.")
        else:
            st.info("No hay datos suficientes.")

# --- 2. AGENDA Y ASISTENCIA (Funcionalidad de Agendar) ---
elif choice == "📅 Agenda y Asistencia":
    st.subheader("📝 Gestión Operativa de Citas")
    
    t1, t2 = st.tabs(["🆕 Nueva Cita", "✅ Confirmar Asistencia"])
    
    with t1:
        with st.form("form_registro", clear_on_submit=True):
            st.write("### Agendar Servicio")
            col1, col2 = st.columns(2)
            with col1:
                # Los campos en el orden de tu Excel
                mascota = st.text_input("Mascota (Nombre)")
                raza = st.text_input("Raza")
                cliente = st.text_input("Dueño (Nombre)")
                id_tel = st.text_input("Teléfono/ID (Columna E)")
            with col2:
                fecha = st.date_input("Fecha")
                hora = st.time_input("Hora (Columna H)") # Campo nuevo
                canal = st.selectbox("Canal", ["Local", "Volante", "Pauta ads", "WhatsApp", "Instagram"])
                valor = st.number_input("Valor Estimado ($)", min_value=0, step=1000)
            
            if st.form_submit_button("💾 Guardar en Agenda"):
                # Creamos la nueva fila con el formato TOML de tus secrets (service account)
                new_row = pd.DataFrame([{
                    "mascota": mascota,
                    "raza": raza,
                    "fecha": fecha.strftime('%d/%m/%Y'), # Formato DD/MM/AAAA para Excel
                    "cliente": cliente,
                    "id": id_tel,
                    "valor": valor,
                    "Canal": canal,
                    "hora": hora.strftime('%H:%M'), # Campo nuevo
                    "asistencia": "Pendiente" # Estado inicial por defecto
                }])
                
                # Unimos y enviamos la actualización
                updated_df = pd.concat([df, new_row], ignore_index=True)
                
                # USAMOS EL MÉTODconn.update (requiere permiso de Editor)
                try:
                    conn.update(spreadsheet=st.secrets["connections"]["gsheets"]["spreadsheet"], worksheet=sheet_name, data=updated_df)
                    st.success(f"✅ Cita agendada para {mascota} ({fecha.strftime('%d/%m')})")
                    st.cache_data.clear() # Limpia cache para ver el cambio de inmediato
                    st.rerun()
                except Exception as e:
                    st.error(f"Error escribiendo en Excel: {e}")
                    st.info("Asegúrese de que 'martina-bot@crm-martina-490822...' tenga permisos de EDITOR en el Google Sheet.")

    with t2:
        st.write("### Marcar Asistencia de Hoy")
        hoy_str = datetime.now().strftime('%Y-%m-%d')
        # Filtramos citas de hoy que estén Pendientes
        citas_hoy = df[(df['fecha'].dt.strftime('%Y-%m-%d') == hoy_str) & (df['asistencia'] == "Pendiente")]
        
        if not citas_hoy.empty:
            # Ordenamos por hora para facilidad
            citas_hoy = citas_hoy.sort_values('hora')
            
            for index, row in citas_hoy.iterrows():
                # mostramos: Hora - Mascota - Cliente
                hora_cita = row['hora'] if pd.notna(row['hora']) else "S/H"
                c1, c2, c3 = st.columns()
                c1.write(f"⏰ **{hora_cita}** - 🐶 **{row['mascota']}** ({row['cliente']})")
                
                # Creamos claves únicas para los botones
                if c2.button("✅ Confirmar Asistencia", key=f"asist_{index}"):
                    df.at[index, 'asistencia'] = "SÍ"
                    conn.update(spreadsheet=st.secrets["connections"]["gsheets"]["spreadsheet"], worksheet=sheet_name, data=df)
                    st.cache_data.clear()
                    st.rerun()
                if c3.button("❌ No vino", key=f"no_{index}"):
                    df.at[index, 'asistencia'] = "NO"
                    conn.update(spreadsheet=st.secrets["connections"]["gsheets"]["spreadsheet"], worksheet=sheet_name, data=df)
                    st.cache_data.clear()
                    st.rerun()
        else:
            st.info("No hay más citas pendientes para hoy.")

# --- 3. ALERTA DE RETENCIÓN (Para evitar perder clientes) ---
elif choice == "🚨 Alerta de Retención":
    st.subheader("Alerta Preventiva de Fugas")
    st.write("Clientes que no han asistido (SÍ) en los últimos 30 días.")
    
    hoy = datetime.now()
    limite = hoy - timedelta(days=30)
    
    # Obtenemos solo los que asistieron (SÍ) para buscar su última visita real
    df_si = df[df['asistencia'] == "SÍ"].copy()
    
    if not df_si.empty:
        # Agrupamos por cliente e ID (teléfono) y buscamos su última fecha de visita
        ultimas_visitas = df_si.groupby(['cliente', 'id'])['fecha'].max().reset_index()
        
        # Filtramos los que su última fecha es anterior al límite (30 días)
        peligro = ultimas_visitas[ultimas_visitas['fecha'] < limite]
        
        # Ordenamos del más antiguo al más reciente
        peligro = peligro.sort_values('fecha')
        
        if not peligro.empty:
            st.warning(f"⚠️ ¡Atención! Hay {len(peligro)} clientes que requieren acción comercial.")
            
            # Mostramos tabla formateada
            st.table(peligro.rename(columns={'fecha': 'Última Asistencia Efectiva', 'id': 'Teléfono'}))
            st.caption("Estrategia: Escríbeles por WhatsApp ofreciendo un baño de cortesía o descuento por volver.")
        else:
            st.success("🎉 ¡Felicidades! Todos tus clientes están activos en el último mes.")
    else:
        st.info("No hay datos suficientes de asistencia real para calcular retención.")

# --- 4. BUSCADOR TOTAL ---
elif choice == "🔍 Buscador Total":
    st.subheader("Búsqueda General en Base de Datos")
    # Texto de búsqueda (ignorando mayúsculas/minúsculas)
    busqueda = st.text_input("🔍 Buscar por mascota, cliente o teléfono...")
    
    if busqueda:
        # Filtramos en todas las columnas convirtiendo a string
        mask = df.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)
        st.dataframe(df[mask], use_container_width=True, hide_index=True)
        st.caption(f"Se encontraron {len(df[mask])} registros.")
    else:
        # Mostramos la tabla completa ordenada por fecha descendente
        st.dataframe(df.sort_values('fecha', ascending=False), use_container_width=True, hide_index=True)
