# procesador_ia.py
import os
import json
import requests
from pathlib import Path

# =====================================================================
# CONFIGURACIÓN DEL LLM LOCAL
# =====================================================================
OLLAMA_URL = "http://localhost:11434/api/generate"
MODELO_LLM = "llama3" # Podés cambiarlo a gemma2, mistral, etc. según lo que uses

# =====================================================================
# PASO 1: LECTURA Y FRAGMENTACIÓN (CHUNKING)
# =====================================================================
def leer_documento(ruta_archivo):
    """
    Lee el contenido crudo de un archivo. 
    Por ahora soporta .txt. Luego expandiremos a .pdf o .docx.
    """
    ruta = Path(ruta_archivo)
    if not ruta.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {ruta_archivo}")
    
    if ruta.suffix.lower() == '.txt':
        with open(ruta, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        raise ValueError("Formato no soportado en esta fase inicial. Usar .txt")

def fragmentar_texto(texto, chunk_size=800, overlap=150):
    """
    Divide el texto largo en fragmentos más pequeños (chunks) basados en palabras.
    El 'overlap' asegura que no perdamos contexto (ej. un nombre cortado a la mitad) 
    entre el final de un chunk y el principio del siguiente.
    """
    palabras = texto.split()
    chunks = []
    i = 0
    
    while i < len(palabras):
        # Tomar un bloque de palabras
        chunk_palabras = palabras[i : i + chunk_size]
        chunk_texto = " ".join(chunk_palabras)
        chunks.append(chunk_texto)
        
        # Avanzar el índice restando el overlap para crear el solapamiento
        i += (chunk_size - overlap)
        
    return chunks

# =====================================================================
# PASO 2: EXTRACCIÓN (MAP) - SKELETON
# =====================================================================
def consultar_ollama(prompt, modelo=MODELO_LLM):
    """
    Envía el prompt al motor local de Ollama y devuelve la respuesta en texto.
    """
    payload = {
        "model": modelo,
        "prompt": prompt,
        "stream": False
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        return response.json().get("response", "")
    except requests.exceptions.RequestException as e:
        print(f"[!] Error conectando con Ollama local: {e}")
        return None

def extraer_entidades_chunk(chunk_texto):
    """
    Aplica el Prompt de Entidad a un fragmento específico.
    (A iterar en la próxima etapa).
    """
    prompt = f"""
    Sos un asistente legal experto en el sistema acusatorio federal argentino.
    Analizá el siguiente fragmento de una resolución judicial y extraé en formato JSON 
    los actores procesales, el Juez, y el Distrito.
    Si no encontrás un dato, poné "No especificado".
    
    Fragmento:
    {chunk_texto}
    """
    
    respuesta = consultar_ollama(prompt)
    return respuesta

# =====================================================================
# ORQUESTADOR DEL PIPELINE
# =====================================================================
def ejecutar_pipeline(ruta_archivo):
    print(f"--- INICIANDO PROCESAMIENTO DE: {ruta_archivo} ---")
    
    # 1. Leer y Fragmentar
    texto_crudo = leer_documento(ruta_archivo)
    chunks = fragmentar_texto(texto_crudo, chunk_size=500, overlap=100)
    print(f"[*] Documento dividido en {len(chunks)} fragmentos.")
    
    # 2. Extracción (Fase Map)
    resultados_parciales = []
    for i, chunk in enumerate(chunks):
        print(f"[*] Procesando fragmento {i+1}/{len(chunks)} con Ollama...")
        # Descomentar la línea de abajo cuando queramos probar Ollama real
        # resultado = extraer_entidades_chunk(chunk)
        # resultados_parciales.append(resultado)
        
    print("--- FASE 1 Y 2 COMPLETADAS ---")
    return resultados_parciales

if __name__ == "__main__":
    # Script de prueba rápida para verificar el chunking
    # Crear un archivo de prueba temporal
    with open("fallo_prueba.txt", "w", encoding="utf-8") as f:
        f.write("Este es un texto de prueba simulando un fallo judicial muy largo. " * 150)
        
    ejecutar_pipeline("fallo_prueba.txt")
# procesador_ia.py