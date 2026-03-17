# manager.py
import os
import sys
import shutil
import pandas as pd
import sqlite3
import uuid
from pathlib import Path

def inicializar_entorno():
    repo_dir = Path("repositorio_archivos")
    if not repo_dir.exists():
        repo_dir.mkdir()
        print(f"[*] Carpeta de repositorio creada: {repo_dir.absolute()}")
    return repo_dir

def buscar_archivo_datos(prefijo="Relevamiento"):
    archivos = []
    for ext in ['.csv', '.xlsx', '.xls']:
        archivos.extend(Path('.').glob(f'{prefijo}*{ext}'))
    
    if not archivos:
        return None
    
    archivos_ordenados = sorted(archivos, key=lambda x: x.stat().st_mtime, reverse=True)
    return archivos_ordenados[0]

def detectar_y_cargar_archivo(ruta_archivo):
    ruta = Path(ruta_archivo)
    if not ruta.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {ruta_archivo}")
    
    extension = ruta.suffix.lower()
    
    if extension == '.csv':
        return pd.read_csv(ruta_archivo)
    elif extension in ['.xls', '.xlsx']:
        return pd.read_excel(ruta_archivo)
    else:
        raise ValueError("Formato no soportado. Debe ser .csv o .xlsx")

def limpiar_datos(df):
    df_clean = df.dropna(how='all').copy()
    
    if 'FECHA' in df_clean.columns:
        df_clean['FECHA'] = pd.to_datetime(df_clean['FECHA'], errors='coerce')
    
    # --- CORRECCIÓN BI ---
    # Mantenemos las columnas como enteros reales que soportan nulos (Int64), no como strings.
    columnas_enteras = ['IdFallo', 'Año', 'AÑO']
    for col in columnas_enteras:
        if col in df_clean.columns:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').astype('Int64')
    
    cols_to_fill = ['Distrito', 'JUEZ/A', 'Temas_se', 'ORGANO JUDICIAL', 'ETAPA PROCESAL']
    for col in cols_to_fill:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].fillna("Sin Especificar")
            
    return df_clean

def actualizar_base_datos(df, db_path="jurisprudencia.db"):
    print(f"[*] Actualizando base de datos SQLite en: {db_path}...")
    conn = sqlite3.connect(db_path)
    df.to_sql('resoluciones', conn, if_exists='replace', index=False)
    conn.close()
    print(f"[*] Éxito. {len(df)} registros insertados.")

def registrar_y_copiar_archivo_multimedia(ruta_origen):
    origen = Path(ruta_origen)
    if not origen.exists():
        print("Error: El archivo de origen no existe.")
        return None
        
    repo_dir = inicializar_entorno()
    id_unico = uuid.uuid4().hex[:8]
    nuevo_nombre = f"doc_{id_unico}{origen.suffix}"
    ruta_destino = repo_dir / nuevo_nombre
    
    shutil.copy2(origen, ruta_destino)
    print(f"[*] Archivo copiado al repositorio: {ruta_destino}")
    return str(ruta_destino)

def main():
    print("--- INICIANDO MANAGER DE DATOS ---")
    inicializar_entorno()
    
    archivo_datos = None
    if len(sys.argv) > 1:
        archivo_datos = Path(sys.argv[1])
        print(f"[*] Archivo indicado por el usuario: {archivo_datos.name}")
    else:
        archivo_datos = buscar_archivo_datos(prefijo="Relevamiento")
        if archivo_datos:
            print(f"[*] Archivo detectado automáticamente: {archivo_datos.name}")
        else:
            print("[!] No se encontraron archivos válidos ('Relevamiento...').")
            return
    
    try:
        df = detectar_y_cargar_archivo(archivo_datos)
        df_limpio = limpiar_datos(df)
        actualizar_base_datos(df_limpio)
        print("--- PROCESO COMPLETADO ---")
    except Exception as e:
        print(f"[!] Error durante la ejecución: {e}")

if __name__ == "__main__":
    main()
# manager.py