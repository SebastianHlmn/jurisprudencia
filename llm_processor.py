# llm_processor.py
import json
import time
import sqlite3
import requests
import pandas as pd

# Configuración de Ollama (Motor local)
OLLAMA_URL = "http://localhost:11434/api/generate"
MODELO_LLM = "gemma:2b" 

def procesar_resolucion_con_llm(texto):
    """Envía el texto al LLM local vía Ollama y fuerza una salida en JSON estructurado."""
    prompt = f"""
    Eres un asistente legal experto en el sistema acusatorio federal argentino.
    Analiza la siguiente resolución judicial y extrae la información solicitada estrictamente en formato JSON válido.
    No agregues texto explicativo fuera del JSON, solo devuelve el objeto JSON.
    
    Estructura JSON requerida:
    {{
        "FECHA": "YYYY-MM-DD",
        "Año": YYYY,
        "Distrito": "Nombre del distrito jurisdiccional",
        "ORGANO JUDICIAL": "Nombre del juzgado o tribunal",
        "JUEZ/A": "Nombre del magistrado/a",
        "Temas_se": "Tema principal de la resolución",
        "CASO": "Carátula o nombre del caso",
        "ETAPA PROCESAL": "Etapa del proceso (ej. IPP, Juicio, Revisión)",
        "SUMARIO": "Un resumen claro y conciso de los antecedentes principales y la decisión adoptada"
    }}

    Texto de la resolución:
    {texto}
    """
    
    payload = {
        "model": MODELO_LLM,
        "prompt": prompt,
        "stream": False,
        "format": "json" 
    }
    
    try:
        respuesta = requests.post(OLLAMA_URL, json=payload)
        respuesta.raise_for_status()
        contenido_json = respuesta.json().get('response', '{}')
        datos = json.loads(contenido_json)
        return datos
    except Exception as e:
        return {"error": str(e)}

def insertar_en_sqlite(datos, db_path, table_name):
    """Inserta el diccionario de datos procesados como una nueva fila en SQLite."""
    try:
        conn = sqlite3.connect(db_path)
        df_nuevo = pd.DataFrame([datos])
        
        # Validar y unificar columnas con la tabla existente
        try:
            df_existente = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 1", conn)
            for col in df_existente.columns:
                if col not in df_nuevo.columns:
                    df_nuevo[col] = pd.NA
        except sqlite3.OperationalError:
            pass
        
        # Generar un ID numérico para la métrica del tablero si no existe
        if 'IdFallo' not in df_nuevo.columns:
            df_nuevo['IdFallo'] = int(time.time())
            
        df_nuevo.to_sql(table_name, conn, if_exists='append', index=False)
        conn.close()
        return True
    except Exception:
        return False
# llm_processor.py