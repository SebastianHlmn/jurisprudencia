# ui_ingesta_ia.py
import streamlit as st
import tempfile
import json
import os
from procesador_ia import (
    fragmentar_texto,
    paso_1_map_extraccion,
    paso_2_reduce_consolidacion
)

def render_ui():
    st.header("🧠 Laboratorio de Ingesta de Fallos (IA)")
    st.markdown("Cargá una resolución judicial en texto crudo y dejá que Ollama extraiga automáticamente los metadatos y redacte el sumario.")

    # --- CONFIGURACIÓN ---
    col_conf1, col_conf2 = st.columns(2)
    
    # Podríamos usar la función get_ollama_models del lab de audiencias, por ahora lo dejamos estático
    modelo_elegido = col_conf1.selectbox("Modelo Local (Ollama)", ["llama3", "mistral", "gemma2", "phi3"], index=0)
    
    chunk_size = col_conf2.number_input("Tamaño de Fragmento (Caracteres)", min_value=1000, max_value=8000, value=3500, step=500)
    
    st.divider()

    # --- CARGA DE ARCHIVO ---
    archivo_subido = st.file_uploader("Subir Resolución (.txt)", type=["txt"])
    
    if archivo_subido:
        # Leemos el contenido
        texto_crudo = archivo_subido.read().decode("utf-8")
        
        with st.expander("Ver texto original", expanded=False):
            st.text_area("Contenido:", texto_crudo, height=200, disabled=True)

        if st.button("🚀 Iniciar Procesamiento Mágico", type="primary"):
            
            # --- FASE 1: CHUNKING ---
            st.subheader("Paso 1: Fragmentación")
            with st.spinner("Dividiendo el texto inteligentemente..."):
                chunks = fragmentar_texto(texto_crudo, chunk_size=int(chunk_size), chunk_overlap=400)
                st.success(f"Documento dividido en {len(chunks)} fragmentos.")
            
            # --- FASE 2: MAP (EXTRACCIÓN) ---
            st.subheader("Paso 2: Extracción de Entidades (Fase Map)")
            barra_progreso = st.progress(0, text="Iniciando extracción con LLM...")
            
            resultados_parciales = []
            
            # Simulamos el bucle del paso_1 pero en la UI para mostrar progreso
            from procesador_ia import consultar_ollama, limpiar_json_string
            prompt_template = """
            Sos un asistente legal del Ministerio Público Fiscal.
            Analizá el siguiente fragmento de una resolución judicial y extraé los siguientes datos en formato estricto JSON.
            Si un dato no está presente, asigná el valor null.
            
            Claves del JSON esperadas:
            - "Distrito": (ej. Salta, Rosario, Mendoza)
            - "Juez": (Nombre del juez o jueza)
            - "Organo_Judicial": (ej. Juzgado Federal de Garantías, Cámara)
            - "Etapa_Procesal": (ej. Garantías, Juicio, Ejecución)
            - "Temas": (Lista de strings con los temas, ej. ["Allanamiento", "Nulidad"])
            - "Caso": (Nombre corto o carátula del caso)

            FRAGMENTO A ANALIZAR:
            {texto}
            """
            
            for i, chunk in enumerate(chunks):
                prompt = prompt_template.replace("{texto}", chunk)
                success, response = consultar_ollama(modelo_elegido, prompt, formato="json")
                
                if success:
                    cleaned = limpiar_json_string(response)
                    resultados_parciales.append(cleaned)
                else:
                    st.error(f"Error procesando el fragmento {i+1}")
                    resultados_parciales.append('{"error": "Fallo en modelo"}')
                
                barra_progreso.progress((i + 1) / len(chunks), text=f"Procesando fragmento {i+1}/{len(chunks)}")
            
            with st.expander("Ver JSONs Parciales (Fase Map)", expanded=False):
                for i, res in enumerate(resultados_parciales):
                    st.markdown(f"**Fragmento {i+1}**")
                    st.json(res)

            # --- FASE 3: REDUCE (CONSOLIDACIÓN Y SUMARIO) ---
            st.subheader("Paso 3: Consolidación y Redacción (Fase Reduce)")
            with st.spinner("Unificando datos y redactando el sumario jurídico..."):
                json_final_str = paso_2_reduce_consolidacion(resultados_parciales, modelo_elegido)
                
                try:
                    resultado_diccionario = json.loads(json_final_str)
                    st.success("¡Procesamiento exitoso!")
                    st.json(resultado_diccionario)
                    
                    st.info("💡 En el próximo sprint, conectaremos este resultado para que se inserte directamente en la base de datos SQLite.")
                    
                except Exception as e:
                    st.error("El modelo no devolvió un JSON final válido.")
                    st.text(json_final_str)

# ui_ingesta_ia.py