# ui_herramientas.py
import streamlit as st
import tempfile
import os
import docx
from transcriber import transcribir_archivo_multimedia

def leer_docx(ruta_archivo):
    """Extrae el texto crudo de un documento Microsoft Word."""
    doc = docx.Document(ruta_archivo)
    texto_completo = []
    for para in doc.paragraphs:
        if para.text.strip():
            texto_completo.append(para.text.strip())
    return "\n".join(texto_completo)

def render_ui():
    st.header("🛠️ Herramientas de Ingesta Multimodal")
    st.markdown("Cargá documentos Word, audios o videos de audiencias para transcribirlos, corregirlos y prepararlos para el análisis de IA.")

    tab_docs, tab_media = st.tabs(["📄 Procesar Documentos (Word/TXT)", "🎬 Transcribir Multimedia (Audio/Video)"])

    # ---------------------------------------------------------
    # PESTAÑA 1: LECTURA DE TEXTO Y WORD
    # ---------------------------------------------------------
    with tab_docs:
        archivo_doc = st.file_uploader("Subir Resolución (.txt, .docx)", type=["txt", "docx"], key="doc_up")
        
        if archivo_doc:
            if archivo_doc.name.endswith(".txt"):
                texto_crudo = archivo_doc.read().decode("utf-8")
            elif archivo_doc.name.endswith(".docx"):
                texto_crudo = leer_docx(archivo_doc)
            else:
                texto_crudo = ""
                
            st.success(f"Archivo '{archivo_doc.name}' cargado correctamente.")
            st.info("Revisá y editá el documento si es necesario antes de enviarlo a la IA.")
            
            texto_corregido = st.text_area("Revisar/Editar Texto:", value=texto_crudo, height=300, key="txt_doc")
            
            if st.button("Guardar como texto preparado", key="save_doc"):
                # Lo guardamos en el estado de la sesión para que el módulo de IA lo agarre luego
                st.session_state['texto_preparado_ia'] = texto_corregido
                st.success("¡Texto guardado en memoria! Ya podés ir a la sección 'Ingesta con IA' para procesarlo.")

    # ---------------------------------------------------------
    # PESTAÑA 2: TRANSCRIPCIÓN DE VIDEOS/AUDIOS
    # ---------------------------------------------------------
    with tab_media:
        archivo_media = st.file_uploader("Subir Audiencia (.mp3, .wav, .mp4)", type=["mp3", "wav", "mp4"], key="media_up")
        
        col1, col2 = st.columns(2)
        modelo_whisper = col1.selectbox("Precisión de Transcripción (Modelo Whisper):", ["tiny", "base", "small"], index=1)
        
        if archivo_media:
            if st.button("🎙️ Iniciar Transcripción Local"):
                with st.spinner(f"Extrayendo y transcribiendo con modelo '{modelo_whisper}'... Esto puede demorar según el largo del video."):
                    suffix = os.path.splitext(archivo_media.name)[1]
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                        tmp_file.write(archivo_media.read())
                        ruta_temp = tmp_file.name
                        
                    try:
                        transcripcion_cruda = transcribir_archivo_multimedia(ruta_temp, modelo_whisper=modelo_whisper)
                        st.session_state['transcripcion_temporal'] = transcripcion_cruda
                    except Exception as e:
                        st.error(f"Error durante la transcripción: {e}")
                    finally:
                        if os.path.exists(ruta_temp):
                            os.remove(ruta_temp)
            
            # Flujo de Corrección Manual (El core del Laboratorio de Audiencias)
            if 'transcripcion_temporal' in st.session_state:
                st.success("¡Transcripción completada!")
                st.warning("Paso Crítico: Revisá el texto. Whisper puede confundir nombres propios o jerga legal.")
                
                texto_corregido_media = st.text_area(
                    "Corrección Manual de la Transcripción:", 
                    value=st.session_state['transcripcion_temporal'], 
                    height=400, 
                    key="txt_media"
                )
                
                if st.button("Aprobar Transcripción y Guardar", type="primary"):
                    st.session_state['texto_preparado_ia'] = texto_corregido_media
                    st.success("¡Transcripción aprobada! Lista para la extracción de entidades en 'Ingesta con IA'.")

# ui_herramientas.py