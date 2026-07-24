from datetime import datetime
import io
import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
import pandas as pd
import streamlit as st

# Configuración de página
st.set_page_config(
    page_title="Control de Entregas - SONAMEX", page_icon="📦", layout="wide"
)

# Estilo visual corporativo SONAMEX
PRIMARY_COLOR = "#00512D"  # Verde institucional aproximado
SECONDARY_COLOR = "#F4F6F4"

st.markdown(
    f"""
    <style>
    .main-header {{
        font-size: 24px;
        font-weight: bold;
        color: {PRIMARY_COLOR};
        text-align: center;
        margin-bottom: 20px;
    }}
    .stButton>button {{
        background-color: {PRIMARY_COLOR};
        color: white;
        border-radius: 5px;
        width: 100%;
    }}
    </style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="main-header">📦 Sistema de Control y Medición de Entregas - SONAMEX</div>',
    unsafe_allow_html=True,
)


# Simulación de Base de Datos en Memoria o Conexión (Para este ejemplo usamos st.session_state)
# En producción, esto se conecta fácilmente a Google Sheets mediante gspread o st.connection.
if "db_entregas" not in st.session_state:
    st.session_state.db_entregas = pd.DataFrame(
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

# Menú de Navegación por Roles
menu = st.sidebar.selectbox(
    "Selecciona el Módulo",
    ["1. Oficina (Alta de Envíos)", "2. Campo (Repartidores)", "3. Reportes"],
)

df = st.session_state.db_entregas

# ==========================================
# MÓDULO 1: OFICINA (Alta de Envíos / Layout)
# ==========================================
if menu == "1. Oficina (Alta de Envíos)":
    st.subheader("🏢 Módulo de Atención a Clientes / Oficina")
    st.write(
        "Ingresa los datos del cliente y la entrega para enviarla a ruta."
    )

    with st.form("form_alta"):
        col1, col2 = st.columns(2)
        with col1:
            cliente = st.text_input("Nombre del Cliente")
            telefono = st.text_input("Teléfono de Contacto")
        with col2:
            fecha_asig = st.date_input(
                "Fecha programada", value=datetime.today()
            )
            direccion = st.text_area("Dirección Completa")

        submit_alta = st.form_submit_button("Registrar Envío para Ruta")

        if submit_alta:
            if cliente and direccion:
                nuevo_id = len(df) + 1
                nuevo_registro = {
                    "id": nuevo_id,
                    "fecha_asig": str(fecha_asig),
                    "cliente": cliente,
                    "direccion": direccion,
                    "telefono": telefono,
                    "estatus_entrega": "Pendiente",
                    "motivo": "",
                    "comentarios": "",
                    "fecha_actualizacion": "",
                }
                st.session_state.db_entregas = pd.concat(
                    [df, pd.DataFrame([nuevo_registro])], ignore_index=True
                )
                st.success(
                    f"¡Envío para el cliente '{cliente}' registrado correctamente!"
                )
            else:
                st.error("Por favor completa al menos el nombre y la dirección.")

    st.markdown("---")
    st.subheader("📋 Envíos Actuales en Sistema")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No hay envíos registrados todavía.")

# ==========================================
# MÓDULO 2: CAMPO (Vista de Repartidores)
# ==========================================
elif menu == "2. Campo (Repartidores)":
    st.subheader("📱 Módulo de Reparto en Campo")
    st.write("Selecciona tu entrega pendiente para actualizar su estatus.")

    if df.empty or len(df[df["estatus_entrega"] == "Pendiente"]) == 0:
        st.info("No hay entregas pendientes por actualizar en este momento.")
    else:
        pendientes = df[df["estatus_entrega"] == "Pendiente"]
        # Selector de cliente pendiente
        cliente_seleccionado = st.selectbox(
            "Selecciona el Cliente a actualizar:",
            options=pendientes["cliente"].tolist(),
        )

        # Filtrar el registro actual
        registro_idx = df[df["cliente"] == cliente_seleccionado].index[0]
        row = df.loc[registro_idx]

        st.markdown(f"**Dirección:** {row['direccion']}")
        st.markdown(f"**Teléfono:** {row['telefono']}")

        with st.form("form_campo"):
            estatus = st.radio(
                "¿Se entregó el producto?",
                ["Entregado con éxito", "No se entregó"],
            )

            motivo = ""
            if estatus == "No se entregó":
                motivo = st.selectbox(
                    "Motivo de no entrega",
                    [
                        "Cliente ausente",
                        "Negocio cerrado",
                        "Dirección incorrecta",
                        "Reprogramado por cliente",
                        "Otro",
                    ],
                )

            comentarios = st.text_area(
                "Comentarios adicionales (Ej. Pide entregar por la tarde, regresa a las 3 pm)"
            )

            submit_campo = st.form_submit_button("Guardar Estatus de Entrega")

            if submit_campo:
                st.session_state.db_entregas.at[
                    registro_idx, "estatus_entrega"
                ] = estatus
                st.session_state.db_entregas.at[registro_idx, "motivo"] = motivo
                st.session_state.db_entregas.at[
                    registro_idx, "comentarios"
                ] = comentarios
                st.session_state.db_entregas.at[
                    registro_idx, "fecha_actualizacion"
                ] = str(datetime.now())
                st.success(
                    "¡Información de campo actualizada con éxito! Buen trabajo."
                )
                st.rerun()

# ==========================================
# MÓDULO 3: REPORTES (Excel con estilo Sonamex)
# ==========================================
elif menu == "3. Reportes":
    st.subheader("📊 Módulo de Reportería y Exportación")
    st.write(
        "Selecciona el rango de fechas para generar el reporte descargable en Excel."
    )

    if df.empty:
        st.warning("No hay datos disponibles para generar reportes.")
    else:
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            f_inicio = st.date_input("Fecha Inicial", value=datetime.today())
        with col_f2:
            f_fin = st.date_input("Fecha Final", value=datetime.today())

        if st.button("📥 Generar Reporte Excel con Estilo SONAMEX"):
            # Filtrado por fecha (simulado en base a la fecha de asignación)
            df_filtrado = df.copy()

            # Creación del archivo Excel usando OpenPyXL para dar formato institucional
            output = io.BytesIO()
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Reporte de Entregas"

            # Estilos institucionales
            header_fill = PatternFill(
                start_color="00512D", end_color="00512D", fill_type="solid"
            )
            header_font = Font(
                name="Calibri", size=11, bold=True, color="FFFFFF"
            )
            border_thin = Border(
                left=Side(style="thin", color="CCCCCC"),
                right=Side(style="thin", color="CCCCCC"),
                top=Side(style="thin", color="CCCCCC"),
                bottom=Side(style="thin", color="CCCCCC"),
            )

            # Título del Reporte
            ws.append(["REPORTE DE ENTREGAS - SONAMEX S.A. DE C.V."])
            ws.append(
                [
                    f"Generado del {f_inicio} al {f_fin} | Fecha de emisión: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                ]
            )
            ws.append([])  # Espacio

            # Encabezados de tabla
            headers = [
                "ID",
                "Fecha Asignación",
                "Cliente",
                "Dirección",
                "Teléfono",
                "Estatus",
                "Motivo",
                "Comentarios",
                "Última Actualización",
            ]
            ws.append(headers)

            # Dar estilo a la cabecera de la tabla (Fila 4)
            for col_num in range(1, len(headers) + 1):
                cell = ws.cell(row=4, column=col_num)
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(
                    horizontal="center", vertical="center"
                )

            # Agregar datos
            for row_idx, row in df_filtrado.iterrows():
                ws.append(list(row))
                current_row = ws.max_row
                for col_num in range(1, len(headers) + 1):
                    cell = ws.cell(row=current_row, column=col_num)
                    cell.border = border_thin
                    cell.alignment = Alignment(
                        horizontal="left", vertical="center"
                    )

            # Autoajustar anchos de columna
            for col in ws.columns:
                max_len = max(len(str(cell.value or "")) for cell in col)
                col_letter = get_column_letter(col[0].column)
                ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

            wb.save(output)
            processed_data = output.getvalue()

            st.download_button(
                label="⬇️ Descargar Archivo Excel (.xlsx)",
                data=processed_data,
                file_name=f"Reporte_Entregas_Sonamex_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            st.success("¡Reporte listo para descargar con éxito!")