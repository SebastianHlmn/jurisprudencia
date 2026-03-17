# config.py
import os

CONFIG = {
    # Rutas y Base de Datos
    "db_path": os.getenv("DB_PATH", "jurisprudencia.db"),
    "table_name": os.getenv("DB_TABLE", "resoluciones"),
    
    # Nomenclaturas y Filtros
    "columnas_filtro": ["Distrito", "JUEZ/A", "Temas", "ORGANO JUDICIAL"],
    "columna_fecha": "FECHA",
    "columna_año": "AÑO",
    "columnas_vista_detalle": ['FECHA', 'Distrito', 'ORGANO JUDICIAL', 'JUEZ/A', 'Temas', 'CASO', 'SUMARIO'],
    
    # Textos de Interfaz
    "app_title": "⚖️ Tablero Dinámico de Jurisprudencia (MPF)",
    
    # Ingesta (Lo usaremos luego para manager.py)
    "prefijo_ingesta": "Relevamiento"
}
# config.py