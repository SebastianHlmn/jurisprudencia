# manager.py
import os
import sys
import shutil
import pandas as pd
import sqlite3
import uuid
from pathlib import Path

def inicializar_entorno():
    """
    Crea la carpeta plana para los archivos si no existe.
    """
    repo_dir = Path("repositorio_archivos")
    if not repo_dir.exists():
        repo_dir.mkdir()
        print(f"[*] Carpeta de repositorio creada: {repo_dir.absolute()}")
    return repo_dir

def buscar_archivo_datos(prefijo="Relevamiento"):
    """
    Busca automáticamente el archivo .csv o .xlsx más reciente en el directorio actual
    QUE EMPIECE con el prefijo indicado, para evitar procesar exportaciones u otros archivos.
    """
    archivos = []
    # Buscamos solo los archivos que coincidan con el prefijo
    for ext in ['.csv', '.xlsx', '.xls']:
        archivos.extend(Path('.').glob(f'{prefijo}*{ext}'))
    
    if not archivos:
        return None
    
    # Ordenar por fecha de modificación (el más reciente primero)
    archivos_ordenados = sorted(archivos, key=lambda x: x.stat().st_mtime, reverse=True)
    return archivos_ordenados[0]

def detectar_y_cargar_archivo(ruta_archivo):
    """
    Detecta si es Excel o CSV y lo carga en un DataFrame.
    """
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
    """
    Aplica las reglas de limpieza y formateo de fechas.
    """
    df_clean = df.dropna(how='all').copy()
    
    if 'FECHA' in df_clean.columns:
        df_clean['FECHA'] = pd.to_datetime(df_clean['FECHA'], errors='coerce')
        df_clean['AÑO'] = df_clean['FECHA'].dt.year
    
    cols_to_fill = ['Distrito', 'JUEZ/A', 'Temas', 'ETAPA PROCESAL', 'ORGANO JUDICIAL']
    for col in cols_to_fill:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].fillna("Sin Especificar")
            
    return df_clean

def actualizar_base_datos(df, db_path="jurisprudencia.db"):
    """
    Reemplaza la tabla en SQLite con el DataFrame procesado.
    """
    print(f"[*] Actualizando base de datos SQLite en: {db_path}...")
    conn = sqlite3.connect(db_path)
    df.to_sql('resoluciones', conn, if_exists='replace', index=False)
    conn.close()
    print(f"[*] Éxito. {len(df)} registros insertados.")

def registrar_y_copiar_archivo_multimedia(ruta_origen):
    """
    Función utilitaria para copiar un PDF/Audio al repositorio plano 
    sin riesgo de colisiones, devolviendo la ruta final para guardarla en la DB.
    """
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
    
    # 1. Chequear si se pasó un archivo por línea de comandos
    if len(sys.argv) > 1:
        archivo_datos = Path(sys.argv[1])
        print(f"[*] Archivo indicado por el usuario: {archivo_datos.name}")
    else:
        # 2. Búsqueda automática del más reciente con el prefijo seguro
        archivo_datos = buscar_archivo_datos(prefijo="Relevamiento")
        if archivo_datos:
            print(f"[*] Archivo detectado automáticamente (el más reciente válido): {archivo_datos.name}")
        else:
            print("[!] No se encontraron archivos válidos (que empiecen con 'Relevamiento') en el directorio actual.")
            print("[!] Uso manual: python manager.py [nombre_del_archivo]")
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