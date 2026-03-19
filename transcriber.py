# transcriber.py
import os
import tempfile
import whisper
from moviepy.editor import VideoFileClip

def extract_audio(video_path, output_audio_path):
    """Extrae la pista de audio de un archivo de video usando MoviePy."""
    try:
        video = VideoFileClip(video_path)
        video.audio.write_audiofile(output_audio_path, verbose=False, logger=None)
        video.close()
        return output_audio_path
    except Exception as e:
        raise RuntimeError(f"Error extrayendo audio del video: {e}")

def transcribir_archivo_multimedia(ruta_archivo, modelo_whisper="base"):
    """
    Detecta el tipo de archivo, extrae el audio si es necesario, 
    y utiliza Whisper local para generar la transcripción en texto.
    """
    ext = os.path.splitext(ruta_archivo)[1].lower()
    
    archivo_procesar = ruta_archivo
    temp_audio_path = None
    
    # Si es video, extraemos el audio temporalmente para Whisper
    if ext in ['.mp4', '.mkv', '.avi', '.mov']:
        temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        temp_audio_path = temp_audio.name
        temp_audio.close()
        
        print(f"[*] Extrayendo audio del video: {ruta_archivo}")
        archivo_procesar = extract_audio(ruta_archivo, temp_audio_path)
        
    print(f"[*] Cargando modelo Whisper '{modelo_whisper}'...")
    model = whisper.load_model(modelo_whisper)
    
    print(f"[*] Iniciando transcripción...")
    # Forzamos idioma español para mejorar la precisión en audiencias
    result = model.transcribe(archivo_procesar, language="es")
    
    # Limpiar archivo temporal de audio si se creó
    if temp_audio_path and os.path.exists(temp_audio_path):
        try:
            os.remove(temp_audio_path)
        except OSError:
            pass
            
    return result["text"]

if __name__ == "__main__":
    print("Módulo transcriber_ia listo para usarse.")
# transcriber.py