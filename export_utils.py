# export_utils.py
import io
from docx import Document
from docx.shared import Inches

def generar_word_dinamico(df_data, reportes_graficos, config):
    """
    Genera un informe en Word con los datos filtrados y los gráficos creados por el usuario.
    """
    doc = Document()
    doc.add_heading(config["app_title"], 0)
    
    # --- Resumen de Datos ---
    doc.add_heading('Resumen de Datos', level=1)
    doc.add_paragraph(f"Total de Registros en esta vista: {len(df_data)}")
    
    for col in config["columnas_filtro"]:
        if col in df_data.columns:
            doc.add_paragraph(f"{col} Distintos: {df_data[col].nunique()}")
    
    # --- Visualizaciones Dinámicas ---
    if reportes_graficos:
        doc.add_heading('Visualizaciones', level=1)
        for titulo, fig in reportes_graficos:
            doc.add_heading(titulo, level=2)
            img_bytes = fig.to_image(format="png")
            doc.add_picture(io.BytesIO(img_bytes), width=Inches(6))
            doc.add_paragraph() # Espacio entre gráficos
        
    # --- Retorno en memoria ---
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    
    return buffer
# export_utils.py