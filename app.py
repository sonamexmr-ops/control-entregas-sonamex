import streamlit as pd_st # Solo para evitar conflicto de nombres con pandas
import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime
import io

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Control de Entregas - Sonamex",
    page_icon="📦",
    layout="wide"
)

# URL DE TU GOOGLE SHEETS WEB APP
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbyJoTXFLLcbDMOrZj6S-nUJdtinMXicGrYU19ze1CavCmbJuI1817VXbyB5SNjj8reR2A/exec"

# RUTA DEL LOGOTIPO EN EL REPOSITORIO DE GITHUB
# (Asegúrate de subir tu imagen con este nombre exacto a tu repositorio o cámbialo aquí)
LOGO_PATH = "logo_sonamex.png"

# --- ESTILOS VISUALES Y COLORES SONAMEX ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button {
        background-color: #003366;
        color: white;
        border-radius: 5px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #002244;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# --- FUNCIONES DE CONEXIÓN CON GOOGLE SHEETS ---
@st.cache_data(ttl=5)
def cargar_datos():
    try:
        response = requests.get(WEB_APP_URL)
        if response.status_code == 200:
            data = response.json()
            if data:
                return pd.DataFrame(data)
        return pd.DataFrame(columns=[
            "id", "fecha_asignacion", "cliente", "direccion", "telefono", 
            "estatus_entrega", "motivo", "comentarios", "fecha_actualizacion"
        ])
    except Exception as e:
        st.error(f"Error al conectar con Google Sheets: {e}")
        return pd.DataFrame()

def guardar_dato(payload):
    try:
        headers = {'Content-Type': 'application/json'}
        response = requests.post(WEB_APP_URL, data=json.dumps(payload), headers=headers)
        return response.status_code == 200
    except Exception as e:
        st.error(f"Error al guardar en Google Sheets: {e}")
        return False

# --- GESTIÓN DE USUARIOS Y SESIÓN ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
    if "usuario" not in st.session_state:
        st.session_state.usuario = ""
    if "rol" not in st.session_state:
        st.session_state.rol = ""

# PANTALLA DE LOGIN
if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Intentar mostrar el logo en la pantalla de login si existe
        try:
            st.image(LOGO_PATH, width=220)
        except:
            st.markdown("<h2 style='text-align: center; color: #003366;'>SONAMEX</h2>", unsafe_allow_html=True)
            
        st.markdown("<h3 style='text-align: center; color: #003366;'>Control de Entregas</h3>", unsafe_allow_html=True)
        st.markdown("<h5 style='text-align: center; color: gray;'>Inicie sesión con sus credenciales</h5>", unsafe_allow_html=True)
        
        usuario_input = st.text_input("Usuario")
        password_input = st.text_input("Contraseña", type="password")
        
        if st.button("Ingresar al Sistema", use_container_width=True):
            usuarios_validos = {
                "admin": {"pass": "master2026", "rol": "Oficina"},
                "oficina1": {"pass": "sonamex2026", "rol": "Oficina"},
                "repartor1": {"pass": "ruta123", "rol": "Campo"}
            }
            
            if usuario_input in usuarios_validos and usuarios_validos[usuario_input]["pass"] == password_input:
                st.session_state.autenticado = True
                st.session_state.usuario = usuario_input
                st.session_state.rol = usuarios_validos[usuario_input]["rol"]
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos")
    st.stop()

# --- BARRA LATERAL CON LOGO Y SESIÓN ---
try:
    st.sidebar.image(LOGO_PATH, width=180)
except:
    st.sidebar.title("📦 SONAMEX")

st.sidebar.write(f"**Usuario:** {st.session_state.usuario}")
st.sidebar.write(f"**Rol:** {st.session_state.rol}")

if st.sidebar.button("Cerrar Sesión"):
    st.session_state.autenticado = False
    st.session_state.usuario = ""
    st.session_state.rol = ""
    st.rerun()

st.sidebar.markdown("---")

# Cargar datos actuales de Google Sheets
df = cargar_datos()

# Asegurar columnas base si el DataFrame viene vacío
columnas_necesarias = ["id", "fecha_asignacion", "cliente", "direccion", "telefono", "estatus_entrega", "motivo", "comentarios", "fecha_actualizacion"]
for col in columnas_necesarias:
    if col not in df.columns:
        df[col] = ""

# --- VISTA SEGÚN EL ROL ---
rol_actual = st.session_state.rol

if rol_actual == "Oficina":
    st.sidebar.subheader("Menú de Oficina")
    menu = st.sidebar.radio("Seleccione opción:", ["1. Alta de Envíos", "2. Histórico y Reportes"])
    
    if menu == "1. Alta de Envíos":
        st.title("🏢 Oficina: Alta y Registro de Envíos")
        st.write("Ingrese los datos del cliente para despachar el envío a ruta.")
        
        with st.form("form_alta"):
            cliente = st.text_input("Nombre del Cliente")
            direccion = st.text_area("Dirección completa")
            telefono = st.text_input("Teléfono de contacto")
            
            submitted = st.form_submit_button("Registrar Envío en Google Sheets")
            
            if submitted:
                if cliente and direccion:
                    nuevo_id = str(int(datetime.now().timestamp()))
                    fecha_hoy = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    payload = {
                        "id": nuevo_id,
                        "fecha_asignacion": fecha_hoy,
                        "cliente": cliente,
                        "direccion": direccion,
                        "telefono": telefono,
                        "estatus_entrega": "Pendiente",
                        "motivo": "",
                        "comentarios": "",
                        "fecha_actualizacion": fecha_hoy
                    }
                    
                    if guardar_dato(payload):
                        st.success("¡Envío registrado correctamente y sincronizado en Google Sheets!")
                        st.cache_data.clear()
                    else:
                        st.error("Hubo un error al guardar el envío.")
                else:
                    st.warning("Por favor complete al menos el nombre del cliente y la dirección.")
                    
    elif menu == "2. Histórico y Reportes":
        st.title("📊 Oficina: Histórico General y Reportes")
        st.write("Visualización total de envíos y filtrado por fechas para exportar en Excel con formato corporativo.")
        
        if not df.empty and "fecha_asignacion" in df.columns:
            st.subheader("Filtrar Reporte por Fecha de Asignación")
            
            df['solo_fecha'] = pd.to_datetime(df['fecha_asignacion'], errors='coerce').dt.date
            
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                fecha_inicio = st.date_input("Fecha Inicio", value=datetime.now().date())
            with col_f2:
                fecha_fin = st.date_input("Fecha Fin", value=datetime.now().date())
                
            df_filtrado = df[(df['solo_fecha'] >= fecha_inicio) & (df['solo_fecha'] <= fecha_fin)]
            
            st.dataframe(df_filtrado.drop(columns=['solo_fecha']), use_container_width=True)
            
            # Botón de exportación a Excel con diseño institucional Sonamex
            if not df_filtrado.empty:
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_limpio = df_filtrado.drop(columns=['solo_fecha'])
                    df_limpio.to_excel(writer, index=False, sheet_name='Entregas_Sonamex')
                    
                    # Formato corporativo (Excel estético)
                    workbook = writer.book
                    worksheet = writer.sheets['Entregas_Sonamex']
                    
                    header_format = workbook.add_format({
                        'bold': True,
                        'text_wrap': True,
                        'valign': 'top',
                        'fg_color': '#003366',
                        'font_color': '#FFFFFF',
                        'border': 1
                    })
                    
                    for col_num, value in enumerate(df_limpio.columns.values):
                        worksheet.write(0, col_num, value, header_format)
                
                excel_data = output.getvalue()
                
                st.download_button(
                    label="📥 Descargar Reporte en Excel (Sonamex)",
                    data=excel_data,
                    file_name=f"Reporte_Entregas_Sonamex_{fecha_inicio}_al_{fecha_fin}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        else:
            st.info("No hay registros disponibles en el histórico todavía.")

elif rol_actual == "Campo":
    st.title("📱 Campo: Gestión de Ruta del Día")
    st.write("Visualice sus entregas pendientes y registre el estatus en tiempo real.")
    
    fecha_hoy_str = datetime.now().strftime("%Y-%m-%d")
    
    if not df.empty and "fecha_asignacion" in df.columns:
        df['solo_fecha'] = pd.to_datetime(df['fecha_asignacion'], errors='coerce').dt.strftime("%Y-%m-%d")
        df_campo = df[(df['solo_fecha'] == fecha_hoy_str) & (df['estatus_entrega'] == "Pendiente")]
        
        if df_campo.empty:
            st.info("No tienes envíos pendientes asignados para el día de hoy.")
        else:
            st.subheader("Seleccione el envío a gestionar:")
            clientes_pendientes = df_campo['cliente'].tolist()
            cliente_seleccionado = st.selectbox("Cliente / Dirección", clientes_pendientes)
            
            fila_cliente = df_campo[df_campo['cliente'] == cliente_seleccionado].iloc[0]
            
            st.markdown("---")
            st.write(f"**Dirección:** {fila_cliente['direccion']}")
            st.write(f"**Teléfono:** {fila_cliente['telefono']}")
            
            with st.form("form_campo"):
                estatus = st.selectbox("¿Se entregó?", ["Pendiente", "Entregado con éxito", "No entregado / Reprogramado"])
                motivo = st.selectbox("Motivo (si aplica)", ["", "Cliente ausente", "Dirección incorrecta", "Negativa de recibir", "Reprogramado por el cliente", "Otro"])
                comentarios = st.text_area("Comentarios de campo (ej. Pide entregar por la tarde, regreso a las 3 PM)")
                
                guardar_entrega = st.form_submit_button("Guardar Estatus de Entrega")
                
                if guardar_entrega:
                    fecha_act = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    payload = {
                        "id": str(fila_cliente['id']),
                        "fecha_asignacion": str(fila_cliente['fecha_asignacion']),
                        "cliente": str(fila_cliente['cliente']),
                        "direccion": str(fila_cliente['direccion']),
                        "telefono": str(fila_cliente['telefono']),
                        "estatus_entrega": estatus,
                        "motivo": motivo,
                        "comentarios": comentarios,
                        "fecha_actualizacion": fecha_act
                    }
                    
                    if guardar_dato(payload):
                        st.success("¡Estatus actualizado con éxito en Google Sheets!")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("Error al actualizar los datos.")
    else:
        st.info("No hay datos cargados en el sistema.")
