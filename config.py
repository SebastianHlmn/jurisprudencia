# config.py
import os

CONFIG = {
    # Rutas y Base de Datos
    "db_path": os.getenv("DB_PATH", "jurisprudencia.db"),
    "table_name": os.getenv("DB_TABLE", "resoluciones"),
    
    # Nomenclaturas y Filtros ajustados al nuevo CSV
    "columnas_filtro": ["Distrito", "JUEZ/A", "Temas_se", "ORGANO JUDICIAL", "ETAPA PROCESAL"],
    "columna_fecha": "FECHA",
    "columna_año": "Año",
    "columnas_vista_detalle": ['IdFallo', 'FECHA', 'Distrito', 'ORGANO JUDICIAL', 'JUEZ/A', 'Temas_se', 'CASO', 'SUMARIO'],
    
    # Textos de Interfaz (Simples y directos)
    "app_title": "Tablero de Jurisprudencia",
    
    # Ingesta
    "prefijo_ingesta": "Relevamiento"
}
# config.py