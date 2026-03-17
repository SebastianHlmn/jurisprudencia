# app.py
import os
import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px

from config import CONFIG
from export_utils import generar_word_dinamico

def inicializar_sesion():
    if 'filtros_activos' not in st.session_state:
        st.session_state['filtros_activos'] = {}
    if 'reportes' not in st.session_state:
        # Guardará tuplas de (titulo, objeto_figura)
        st.session_state['reportes'] = [] 

@st.cache_data(ttl=300)
def load_data_from_db(db_path, table_name):
    if not os.path.exists(db_path):
        return pd.DataFrame()
    
    try:
        conn = sqlite3.connect(db_path)
        query = f"SELECT * FROM {table_name}"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error de conexión a la base de datos: {e}")
        return pd.DataFrame()

def main():
    st.set_page_config(page_title=CONFIG["app_title"], layout="wide")
    inicializar_sesion()
    
    st.title(CONFIG["app_title"])
    
    df = load_data_from_db(CONFIG["db_path"], CONFIG["table_name"])
    
    if df.empty:
        st.warning("No hay datos. Por favor, ejecute manager.py para cargar la base.")
        st.stop()

    # --- FILTROS ---
    st.sidebar.header("Filtros")
    df_filtrado = df.copy()
    
    for col in CONFIG["columnas_filtro"]:
        if col in df.columns:
            opciones = sorted(df[col].dropna().astype(str).unique())
            seleccion = st.sidebar.multiselect(f"{col}:", opciones, default=[])
            if seleccion:
                df_filtrado = df_filtrado[df_filtrado[col].isin(seleccion)]

    st.markdown(f"**Registros filtrados:** {len(df_filtrado)}")
    st.divider()

    # --- CONSTRUCTOR DE REPORTES (Tipo Tabla Dinámica) ---
    st.markdown("### Constructor de Visualizaciones")
    
    col_var, col_tipo, col_btn = st.columns([2, 2, 1])
    
    # Excluir columnas de texto largo o identificadores únicos de las opciones de agrupación
    exclusiones = ['IdFallo', 'CASO', 'CASO.1', 'SUMARIO', 'RUTA / REFERNCIA EN U', 'NOTAS']
    opciones_agrupacion = [c for c in df_filtrado.columns if c not in exclusiones]
    
    variable_x = col_var.selectbox("Agrupar por variable:", opciones_agrupacion)
    tipo_grafico = col_tipo.selectbox("Formato visual:", ["Barras", "Líneas", "Dona"])
    
    if col_btn.button("Agregar a Reporte"):
        # Preparar datos para el gráfico
        df_grp = df_filtrado[variable_x].value_counts().reset_index()
        df_grp.columns = [variable_x, 'Cantidad']
        df_grp = df_grp.dropna()
        
        titulo_grafico = f"Distribución por {variable_x}"
        
        # Generar figura según elección
        if tipo_grafico == "Barras":
            fig = px.bar(df_grp.sort_values('Cantidad', ascending=True), 
                         x='Cantidad', y=variable_x, orientation='h', 
                         title=titulo_grafico, template="plotly_white")
        elif tipo_grafico == "Líneas":
            df_grp_sorted = df_grp.sort_values(variable_x) # Mejor para fechas/años
            fig = px.line(df_grp_sorted, x=variable_x, y='Cantidad', markers=True, 
                          title=titulo_grafico, template="plotly_white")
        elif tipo_grafico == "Dona":
            fig = px.pie(df_grp, names=variable_x, values='Cantidad', hole=0.4, 
                         title=titulo_grafico, template="plotly_white")
            
        st.session_state['reportes'].append((titulo_grafico, fig))

    # --- MOSTRAR REPORTES GUARDADOS ---
    if st.session_state['reportes']:
        st.markdown("### Reporte Actual")
        if st.button("Limpiar Reporte"):
            st.session_state['reportes'] = []
            st.rerun()
            
        cols_grid = st.columns(2)
        for i, (titulo, fig) in enumerate(st.session_state['reportes']):
            cols_grid[i % 2].plotly_chart(fig, use_container_width=True)
            
    st.divider()

    # --- EXPORTACIÓN ---
    st.markdown("### Generar Informe")
    if st.button("Descargar Informe en Word"):
        with st.spinner("Generando documento..."):
            buffer = generar_word_dinamico(df_filtrado, st.session_state['reportes'], CONFIG)
            st.download_button(
                label="⬇️ Descargar Archivo",
                data=buffer,
                file_name="Informe_Jurisprudencia.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

    st.divider()

    # --- VISTA DE DATOS ---
    st.markdown("### Datos")
    columnas_existentes = [col for col in CONFIG["columnas_vista_detalle"] if col in df_filtrado.columns]
    
    if columnas_existentes:
        st.dataframe(df_filtrado[columnas_existentes], use_container_width=True, hide_index=True)
    else:
        st.dataframe(df_filtrado, use_container_width=True)

if __name__ == "__main__":
    main()
# app.py