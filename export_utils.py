# export_utils.py
import io
from docx import Document
from docx.shared import Inches

def generar_word_dinamico(df_data, fig_year, fig_temas, config):
    """
    Genera un documento Word institucional basado en los datos y gráficos filtrados.
    """
    doc = Document()
    doc.add_heading(config["app_title"], 0)
    
    # --- Resumen Estadístico ---
    doc.add_heading('Resumen Estadístico', level=1)
    doc.add_paragraph(f"Total de Registros: {len(df_data)}")
    
    for col in config["columnas_filtro"]:
        if col in df_data.columns:
            doc.add_paragraph(f"{col} Distintos: {df_data[col].nunique()}")
    
    # --- Gráficos ---
    if fig_year is not None:
        doc.add_heading('Evolución Temporal', level=1)
        img_bytes = fig_year.to_image(format="png")
        doc.add_picture(io.BytesIO(img_bytes), width=Inches(6))
        
    if fig_temas is not None:
        doc.add_heading('Frecuencias Principales', level=1)
        img_bytes = fig_temas.to_image(format="png")
        doc.add_picture(io.BytesIO(img_bytes), width=Inches(6))
        
    # --- Retorno en memoria ---
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    
    return buffer
# export_utils.py