import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import io

# Configuración de la página
st.set_page_config(
    page_title="Control de Entregas - Sonamex",
    page_icon="📦",
    layout="wide"
)

# Estilos y Colores Institucionales Sonamex (Azul Marino #003366)
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
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
    h1, h2, h3 {
        color: #003366;
    }
    </style>
""", unsafe_allow_html=True)

# Configuración de Google Sheets
@st.cache_resource
py_connection = None

def conectar_gsheets():
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        # Usando los secretos configurados en Streamlit Cloud
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        # URL o Nombre de la hoja en los secretos
        sheet_url = st.secrets["sheet_url"]
        sheet = client.open_by_url(sheet_url).sheet1
        return sheet
    except Exception as e:
        st.error(f"Error al conectar con Google Sheets: {e}")
        return None

# Inicializar sesión de autenticación
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.usuario = ""
    st.session_state.rol = ""

# Pantalla de Login
if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("logo_sonamex.png", width=200) if "logo_sonamex.png" else None
        st.title("Control de Entregas Sonamex")
        st.subheader("Iniciar Sesión")
        
        usuario = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        
        if st.button("Ingresar"):
            # Credenciales de usuarios
            if usuario == "admin" and password == "master2026":
                st.session_state.autenticado = True
                st.session_state.usuario = "Admin Máster"
                st.session_state.rol = "Oficina"
                st.rerun()
            elif usuario == "oficina1" and password == "sonamex2026":
                st.session_state.autenticado = True
                st.session_state.usuario = "Oficina 1"
                st.session_state.rol = "Oficina"
                st.rerun()
            elif usuario == "repartor1" and password == "ruta123":
                st.session_state.autenticado = True
                st.session_state.usuario = "Repartidor 1"
                st.session_state.rol = "Campo"
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos")
    st.stop()

# Barra lateral con información de usuario y botón de salida
with st.sidebar:
    st.image("logo_sonamex.png", width=150)
    st.write(f"**Usuario:** {st.session_state.usuario}")
    st.write(f"**Rol:** {st.session_state.rol}")
    if st.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

# Conexión a la hoja
sheet = conectar_gsheets()

if sheet:
    # Obtener datos actuales
    data = sheet.get_all_records()
    columnas_esperadas = ["ID", "Fecha", "Cliente", "Dirección", "Teléfono", "Estatus", "Motivo / Comentarios"]
    
    if not data:
        # Si la hoja está vacía, inicializamos los encabezados
        sheet.append_row(columnas_esperadas)
        df = pd.DataFrame(columns=columnas_esperadas)
    else:
        df = pd.DataFrame(data)
        # Verificar que existan todas las columnas necesarias para evitar errores
        for col in columnas_esperadas:
            if col not in df.columns:
                df[col] = ""

    # ================= ROL: OFICINA (Administración Total) =================
    if st.session_state.rol == "Oficina":
        st.title("🏢 Panel de Control - Oficina")
        
        menu = st.sidebar.selectbox("Menú Oficina", ["1. Alta de Envíos", "2. Histórico y Reportes", "3. Ver Google Sheets"])
        
        if menu == "1. Alta de Envíos":
            st.subheader("Registrar Nuevo Envío")
            with st.form("form_envio"):
                cliente = st.text_input("Nombre del Cliente")
                direccion = st.text_input("Dirección")
                telefono = st.text_input("Teléfono")
                fecha_envio = st.date_input("Fecha Programada", value=datetime.now())
                
                submitted = st.form_submit_button("Registrar Envío")
                if submitted:
                    if cliente and direccion:
                        nuevo_id = str(len(df) + 1)
                        nuevo_registro = [
                            nuevo_id, 
                            str(fecha_envio), 
                            cliente, 
                            direccion, 
                            telefono, 
                            "Pendiente", 
                            ""
                        ]
                        sheet.append_row(nuevo_registro)
                        st.success(f"¡Envío para {cliente registrado con éxito!")
                        st.rerun()
                    else:
                        st.warning("Por favor completa al menos el nombre del cliente y la dirección.")

        elif menu == "2. Histórico y Reportes":
            st.subheader("Histórico General y Reportes por Rango de Fechas")
            
            if not df.empty:
                # Filtro por rango de fechas
                min_date = datetime.today().date()
                max_date = datetime.today().date()
                
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    fecha_inicio = st.date_input("Fecha Inicio", value=min_date)
                with col_f2:
                    fecha_fin = st.date_input("Fecha Fin", value=max_date)
                
                # Filtrar dataframe por fecha si es posible
                try:
                    df['Fecha_dt'] = pd.to_datetime(df['Fecha']).dt.date
                    df_filtrado = df[(df['Fecha_dt'] >= fecha_inicio) & (df['Fecha_dt'] <= fecha_fin)]
                except:
                    df_filtrado = df

                st.dataframe(df_filtrado, use_container_width=True)
                
                # Exportar a Excel con formato corporativo
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_filtrado.to_excel(writer, index=False, sheet_name='Reporte_Entregas')
                output.seek(0)
                
                st.download_button(
                    label="📥 Descargar Reporte en Excel (.xlsx)",
                    data=output,
                    file_name=f"Reporte_Entregas_{fecha_inicio}_al_{fecha_fin}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.info("Aún no hay registros en el sistema.")

        elif menu == "3. Ver Google Sheets":
            st.subheader("Base de Datos en Tiempo Real")
            st.markdown(f"[🔗 Haz clic aquí para abrir tu Google Sheets directamente]({st.secrets['sheet_url']})")
            if not df.empty:
                st.dataframe(df, use_container_width=True)

    # ================= ROL: CAMPO (Repartidor) =================
    elif st.session_state.rol == "Campo":
        st.title("📱 Módulo de Reparto - Campo")
        st.info("Visualizando únicamente los pendientes correspondientes al día de hoy.")
        
        hoy_str = datetime.today().strftime('%Y-%m-%d')
        
        # Filtrar solo pendientes del día actual
        if not df.empty and 'Fecha' in df.columns:
            pendientes_hoy = df[(df['Fecha'] == hoy_str) & (df['Estatus'] == "Pendiente")]
            
            if pendientes_hoy.empty:
                st.success("🎉 ¡Excelente trabajo! No tienes envíos pendientes para el día de hoy.")
            else:
                st.write(f"Tienes **{len(pendientes_hoy)}** envíos pendientes para hoy:")
                
                for idx, row in pendientes_hoy.iterrows():
                    with st.expander(f"📦 {row['Cliente']} - {row['Dirección']}"):
                        st.write(f"**Teléfono:** {row['Teléfono']}")
                        st.write(f"**Fecha:** {row['Fecha']}")
                        
                        with st.form(f"form_reparto_{row['ID']}"):
                            nuevo_estatus = st.selectbox(
                                "Estatus de Entrega", 
                                ["Pendiente", "Entregado con éxito", "No entregado / Reprogramado"],
                                key=f"estatus_{row['ID']}"
                            )
                            motivo_comentario = st.text_area(
                                "Motivo o Comentarios (ej. Pide entregar por la tarde)",
                                key=f"comentario_{row['ID']}"
                            )
                            
                            guardar = st.form_submit_button("Guardar Actualización")
                            if guardar:
                                # Actualizar fila en Google Sheets
                                # Las filas en gspread empiezan en 2 (la 1 son los headers)
                                row_idx = df[df['ID'] == row['ID']].index[0] + 2
                                sheet.update_cell(row_idx, 6, nuevo_estatus) # Columna 6: Estatus
                                sheet.update_cell(row_idx, 7, motivo_comentario) # Columna 7: Motivo
                                st.success("¡Estatus actualizado correctamente en tiempo real!")
                                st.rerun()
        else:
            st.info("No hay información de envíos disponible.")
