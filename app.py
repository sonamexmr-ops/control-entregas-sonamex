import datetime
import requests
import streamlit as st
import pandas as pd
from fpdf import FPDF
import io

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Control de Entregas - Sonamex", page_icon="📦", layout="wide"
)

# URL DE GOOGLE APPS SCRIPT (Conectado a tu Google Sheets)
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbxe-Uz2ZLGYTqP0gH0ByMOIWyrr3LAmKetdZVNyx_xC7sA-H4wtLLGk6l1izJsy_Sswew/exec"


# --- FUNCIONES DE CONEXIÓN CON GOOGLE SHEETS ---
def cargar_datos_gsheets():
  try:
    response = requests.get(WEBHOOK_URL)
    if response.status_code == 200:
      data = response.json()
      if data and isinstance(data, list):
        df = pd.DataFrame(data)
        columnas_requeridas = [
            "id",
            "fecha_asignacion",
            "cliente",
            "direccion",
            "telefono",
            "estatus_entrega",
            "motivo",
            "comentarios",
            "fecha_actualizacion",
        ]
        for col in columnas_requeridas:
          if col not in df.columns:
            df[col] = ""
        return df
  except Exception as e:
    st.error(f"Error al conectar con Google Sheets: {e}")

  # Retornar DataFrame vacío con estructura si falla o no hay datos
  return pd.DataFrame(
      columns=[
          "id",
          "fecha_asignacion",
          "cliente",
          "direccion",
          "telefono",
          "estatus_entrega",
          "motivo",
          "comentarios",
          "fecha_actualizacion",
      ]
  )


def guardar_fila_gsheets(fila_dict):
  try:
    response = requests.post(WEBHOOK_URL, json=fila_dict)
    return response.status_code == 200
  except Exception:
    return False


# --- GESTIÓN DE USUARIOS Y PERFILES ---
USUARIOS = {
    "admin": {"password": "master2026", "rol": "Admin Máster"},
    "oficina1": {"password": "sonamex2026", "rol": "Admin 1"},
    "repartor1": {"password": "ruta123", "rol": "Entregas"},
}

if "autenticado" not in st.session_state:
  st.session_state.autenticado = False
  st.session_state.usuario = ""
  st.session_state.rol = ""

if not st.session_state.autenticado:
  st.markdown(
      "<h2 style='text-align: center;'>📦 Control de Entregas Sonamex</h2>",
      unsafe_allow_html=True,
  )
  st.markdown(
      "<p style='text-align: center;'>Inicia sesión para acceder al"
      " sistema</p>",
      unsafe_allow_html=True,
  )

  col1, col2, col3 = st.columns([1, 2, 1])
  with col2:
    with st.form("login_form"):
      usuario_input = st.text_input("Usuario")
      password_input = st.text_input("Contraseña", type="password")
      submit_login = st.form_submit_button("Entrar")

      if submit_login:
        if (
            usuario_input in USUARIOS
            and USUARIOS[usuario_input]["password"] == password_input
        ):
          st.session_state.autenticado = True
          st.session_state.usuario = usuario_input
          st.session_state.rol = USUARIOS[usuario_input]["rol"]
          st.rerun()
        else:
          st.error("Usuario o contraseña incorrectos")
  st.stop()

# --- INTERFAZ PRINCIPAL (UNA VEZ AUTENTICADO) ---
st.sidebar.title("📦 Menú Sonamex")
st.sidebar.write(
    f"Usuario: **{st.session_state.usuario}** ({st.session_state.rol})"
)

if st.sidebar.button("Cerrar Sesión"):
  st.session_state.autenticado = False
  st.session_state.usuario = ""
  st.session_state.rol = ""
  st.rerun()

# Definir opciones de menú según el rol
if st.session_state.rol in ["Admin Máster", "Admin 1"]:
  menu = st.sidebar.radio(
      "Navegación",
      [
          "1. Oficina (Alta de Envíos)",
          "2. Campo (Estatus de Entregas)",
          "3. Reportes y Exportables",
      ],
  )
else:
  menu = "2. Campo (Estatus de Entregas)"
  st.sidebar.info(
      "Modo Repartidor: Visualizando únicamente los envíos pendientes del"
      " día."
  )

# Cargar datos desde Google Sheets en tiempo real
df_entregas = cargar_datos_gsheets()

# --- MÓDULO 1: OFICINA (ALTA DE ENVÍOS) ---
if menu == "1. Oficina (Alta de Envíos)":
  st.title("🏢 Oficina - Alta de Nuevos Envíos")
  st.write(
      "Registra los datos del cliente para que aparezcan automáticamente en"
      " campo."
  )

  with st.form("form_alta", clear_on_submit=True):
    cliente = st.text_input("Nombre del Cliente")
    direccion = st.text_area("Dirección")
    telefono = st.text_input("Teléfono")
    fecha_asig = st.date_input(
        "Fecha de Asignación / Entrega", datetime.date.today()
    )

    submitted = st.form_submit_button("Registrar Envío")
    if submitted:
      if cliente and direccion:
        # Calcular nuevo ID de forma segura
        if not df_entregas.empty and "id" in df_entregas.columns:
          ids_numericos = pd.to_numeric(df_entregas["id"], errors="coerce")
          nuevo_id = (
              str(int(ids_numericos.max() + 1))
              if not ids_numericos.isna().all()
              else "1"
          )
        else:
          nuevo_id = "1"

        nuevo_registro = {
            "id": nuevo_id,
            "fecha_asignacion": str(fecha_asig),
            "cliente": cliente,
            "direccion": direccion,
            "telefono": telefono,
            "estatus_entrega": "Pendiente",
            "motivo": "",
            "comentarios": "",
            "fecha_actualizacion": str(datetime.datetime.now()),
        }

        if guardar_fila_gsheets(nuevo_registro):
          st.success(
              "¡Envío registrado con éxito y sincronizado con Google Sheets!"
          )
          st.rerun()
        else:
          st.error("Error al guardar en Google Sheets.")
      else:
        st.warning("Por favor completa al menos el cliente y la dirección.")

  st.subheader("📋 Envíos Registrados Recientemente")
  if not df_entregas.empty and not df_entregas["id"].isna().all():
    st.dataframe(
        df_entregas[
            [
                "id",
                "fecha_asignacion",
                "cliente",
                "direccion",
                "telefono",
                "estatus_entrega",
            ]
        ],
        use_container_width=True,
    )
  else:
    st.info("No hay envíos registrados todavía.")

# --- MÓDULO 2: CAMPO (ESTATUS DE ENTREGAS) ---
elif menu == "2. Campo (Estatus de Entregas)":
  st.title("📱 Módulo de Campo - Actualización de Entregas")

  if df_entregas.empty or "id" not in df_entregas.columns or df_entregas["id"].isna().all():
    st.info("No hay entregas registradas en el sistema.")
  else:
    # FILTRO PARA REPARTIDOR: Solo mostrar pendientes del día actual
    if st.session_state.rol == "Entregas":
      hoy_str = str(datetime.date.today())
      df_filtrado = df_entregas[
          (df_entregas["estatus_entrega"] == "Pendiente")
          & (df_entregas["fecha_asignacion"] == hoy_str)
      ]
      st.write(
          f"Mostrando envíos **Pendientes** programados para hoy (**{hoy_str}**):"
      )
    else:
      df_filtrado = df_entregas  # Administradores ven todo para revisión si lo desean

    if df_filtrado.empty:
      st.success(
          "¡Excelente trabajo! No hay entregas pendientes asignadas para el día"
          " de hoy."
      )
    else:
      # Crear lista desplegable legible
      opciones_envios = df_filtrado.apply(
          lambda row: (
              f"ID: {row['id']} | Cliente: {row['cliente']} | Dir:"
              f" {row['direccion']}"
          ),
          axis=1,
      )
      envio_seleccionado = st.selectbox(
          "Selecciona el envío a actualizar:", opciones_envios
      )

      if envio_seleccionado:
        id_sel = envio_seleccionado.split("|")[0].replace("ID:", "").strip()
        fila_actual = df_entregas[df_entregas["id"].astype(str) == id_sel].iloc[
            0
        ]

        st.info(
            f"**Cliente:** {fila_actual['cliente']} \n\n**Dirección:**"
            f" {fila_actual['direccion']} \n\n**Teléfono:**"
            f" {fila_actual['telefono']}"
        )

        with st.form("form_campo"):
          nuevo_estatus = st.selectbox(
              "Estatus de la Entrega",
              [
                  "Pendiente",
                  "Entregado con éxito",
                  "No entregado",
                  "Reprogramado",
              ],
          )
          motivo = st.text_input(
              "Motivo (Opcional, ej. cliente ausente, dirección incorrecta)"
          )
          comentarios = st.text_area(
              "Comentarios (Ej. Pide entregar por la tarde, regreso a las 3 pm)"
          )
          nueva_fecha_reprog = st.date_input(
              "Nueva Fecha (Solo si fue Reprogramado)", datetime.date.today()
          )

          submit_campo = st.form_submit_button("Guardar Actualización")

          if submit_campo:
            # Convertir la serie a diccionario para manipularla
            fila_dict = fila_actual.to_dict()
            fila_dict["estatus_entrega"] = nuevo_estatus
            fila_dict["motivo"] = motivo
            if nuevo_estatus == "Reprogramado":
              fila_dict["comentarios"] = (
                  f"Reprogramado para {nueva_fecha_reprog}. " + comentarios
              )
              fila_dict["fecha_asignacion"] = str(nueva_fecha_reprog)
              fila_dict["estatus_entrega"] = "Pendiente"
            else:
              fila_dict["comentarios"] = comentarios

            fila_dict["fecha_actualizacion"] = str(datetime.datetime.now())

            if guardar_fila_gsheets(fila_dict):
              st.success(
                  "¡Estatus actualizado correctamente en Google Sheets!"
              )
              st.rerun()
            else:
              st.error("Error al actualizar los datos en la nube.")

# --- MÓDULO 3: REPORTES Y EXPORTABLES ---
elif menu == "3. Reportes y Exportables":
  st.title("📊 Reportes y Exportación")
  st.write(
      "Selecciona un rango de fechas para extraer la reportería oficial de"
      " Sonamex."
  )

  if df_entregas.empty or "id" not in df_entregas.columns or df_entregas["id"].isna().all():
    st.info("No hay datos para generar reportes.")
  else:
    col_f1, col_f2 = st.columns(2)
    with col_f1:
      fecha_inicio = st.date_input(
          "Fecha Inicio", datetime.date.today() - datetime.timedelta(days=7)
      )
    with col_f2:
      fecha_fin = st.date_input("Fecha Fin", datetime.date.today())

    # Filtrar por fechas
    df_entregas["fecha_asignacion_dt"] = pd.to_datetime(
        df_entregas["fecha_asignacion"], errors="coerce"
    ).dt.date
    df_reporte = df_entregas[
        (df_entregas["fecha_asignacion_dt"] >= fecha_inicio)
        & (df_entregas["fecha_asignacion_dt"] <= fecha_fin)
    ]

    st.write(
        f"Se encontraron **{len(df_reporte)}** registros en el periodo"
        " seleccionado."
    )
    st.dataframe(df_reporte.drop(columns=["fecha_asignacion_dt"], errors="ignore"), use_container_width=True)

    # Botones de exportación
    col_b1, col_b2 = st.columns(2)

    with col_b1:
      if not df_reporte.empty:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
          df_reporte.drop(columns=["fecha_asignacion_dt"], errors="ignore").to_excel(
              writer, index=False, sheet_name="Reporte Entregas"
          )
        excel_data = output.getvalue()

        st.download_button(
            label="📥 Descargar Reporte en Excel (.xlsx)",
            data=excel_data,
            file_name=f"reporte_entregas_{fecha_inicio}_al_{fecha_fin}.xlsx",
            mime=(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
        )

    with col_b2:
      if not df_reporte.empty:

        def generar_pdf(df):
          pdf = FPDF()
          pdf.add_page()
          pdf.set_font("Arial", "B", 14)
          pdf.cell(
              0,
              10,
              "Reporte de Entregas - Sonamex",
              0,
              1,
              "C",
          )
          pdf.set_font("Arial", "", 10)
          pdf.cell(
              0,
              10,
              f"Periodo: {fecha_inicio} a {fecha_fin}",
              0,
              1,
              "C",
          )
          pdf.ln(5)

          pdf.set_font("Arial", "B", 8)
          pdf.cell(15, 8, "ID", 1)
          pdf.cell(35, 8, "Fecha", 1)
          pdf.cell(50, 8, "Cliente", 1)
          pdf.cell(50, 8, "Estatus", 1)
          pdf.ln()

          pdf.set_font("Arial", "", 8)
          for _, row in df.iterrows():
            pdf.cell(15, 8, str(row["id"]), 1)
            pdf.cell(35, 8, str(row["fecha_asignacion"]), 1)
            pdf.cell(50, 8, str(row["cliente"])[:22], 1)
            pdf.cell(50, 8, str(row["estatus_entrega"]), 1)
            pdf.ln()
          return pdf.output(dest="S").encode("latin1")

        pdf_data = generar_pdf(df_reporte)
        st.download_button(
            label="📥 Descargar Reporte en PDF",
            data=pdf_data,
            file_name=f"reporte
