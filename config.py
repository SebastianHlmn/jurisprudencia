# config.py
import os

CONFIG = {
    "db_path": os.getenv("DB_PATH", "jurisprudencia.db"),
    "table_name": os.getenv("DB_TABLE", "resoluciones"),
    
    # Se agrega "Año" para que el filtro esté visible por defecto
    "columnas_filtro": ["Distrito", "JUEZ/A", "Temas_se", "ORGANO JUDICIAL", "ETAPA PROCESAL", "Año"],
    "columna_fecha": "FECHA",
    "columna_año": "Año",
    "columnas_vista_detalle": ['IdFallo', 'FECHA', 'Distrito', 'ORGANO JUDICIAL', 'JUEZ/A', 'Temas_se', 'CASO', 'SUMARIO'],
    
    "metrica_default": "IdFallo",
    
    "app_title": "Tablero de Jurisprudencia",
    "prefijo_ingesta": "Relevamiento"
}
# config.py