# app.py
import os
import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px

# Importamos nuestros propios módulos modulares
from config import CONFIG
from export_utils import generar_word_dinamico

def inicializar_sesion():
    if 'filtros_activos' not in st.session_state:
        st.session_state['filtros_activos'] = {}
    if 'modo_vista' not in st.session_state:
        st.session_state['modo_vista'] = 'dashboard'

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
    st.set_page_config(page_title=CONFIG["app_title"], page_icon="⚖️", layout="wide")
    inicializar_sesion()
    
    st.title(CONFIG["app_title"])
    
    df = load_data_from_db(CONFIG["db_path"], CONFIG["table_name"])
    
    if df.empty:
        st.warning("No hay datos disponibles. Verificá que el repositorio haya sido inicializado.")
        st.stop()

    # --- BARRA LATERAL DEDICADA A FILTROS DINÁMICOS ---
    st.sidebar.header("Filtros de Búsqueda")
    df_filtrado = df.copy()
    
    for col in CONFIG["columnas_filtro"]:
        if col in df.columns:
            opciones = sorted(df[col].dropna().astype(str).unique())
            seleccion = st.sidebar.multiselect(f"Filtrar por {col}:", opciones, default=[])
            if seleccion:
                df_filtrado = df_filtrado[df_filtrado[col].isin(seleccion)]
                st.session_state['filtros_activos'][col] = seleccion

    # --- KPIs DINÁMICOS ---
    st.markdown("### Resumen Estadístico")
    kpi_cols = st.columns(len(CONFIG["columnas_filtro"]) + 1)
    kpi_cols[0].metric("Total Resoluciones", len(df_filtrado))
    
    for i, col in enumerate(CONFIG["columnas_filtro"]):
        if col in df_filtrado.columns:
            kpi_cols[i+1].metric(f"{col}", df_filtrado[col].nunique())

    st.divider()

    # --- GRÁFICOS ---
    col_graf1, col_graf2 = st.columns(2)
    fig_year = None
    fig_temas = None

    with col_graf1:
        st.markdown("#### Evolución Temporal")
        col_año = CONFIG["columna_año"]
        if col_año in df_filtrado.columns:
            df_year = df_filtrado[col_año].value_counts().reset_index()
            df_year.columns = [col_año, 'Cantidad']
            df_year = df_year.dropna().sort_values(col_año)
            
            if not df_year.empty:
                fig_year = px.line(df_year, x=col_año, y='Cantidad', markers=True, template="plotly_white")
                fig_year.update_xaxes(dtick=1)
                st.plotly_chart(fig_year, use_container_width=True)
            else:
                st.info("Sin datos temporales.")

    with col_graf2:
        st.markdown("#### Distribución Principal")
        col_graf_bar = CONFIG["columnas_filtro"][2] if len(CONFIG["columnas_filtro"]) > 2 else CONFIG["columnas_filtro"][0]
        
        if col_graf_bar in df_filtrado.columns:
            df_bar = df_filtrado[df_filtrado[col_graf_bar] != "Sin Especificar"][col_graf_bar].value_counts().head(10).reset_index()
            df_bar.columns = [col_graf_bar, 'Cantidad']
            
            if not df_bar.empty:
                fig_temas = px.bar(df_bar.sort_values('Cantidad', ascending=True), 
                                   x='Cantidad', y=col_graf_bar, orientation='h', template="plotly_white")
                st.plotly_chart(fig_temas, use_container_width=True)

    st.divider()

    # --- EXPORTACIÓN ---
    st.markdown("### 📄 Exportación Institucional")
    if st.button("Generar Informe en Word"):
        with st.spinner("Compilando reporte dinámico..."):
            buffer = generar_word_dinamico(df_filtrado, fig_year, fig_temas, CONFIG)
            st.download_button(
                label="⬇️ Descargar Archivo Word",
                data=buffer,
                file_name="Reporte_Jurisprudencia_Agil.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

    st.divider()

    # --- VISTA DETALLADA DINÁMICA ---
    st.markdown("### Base de Resoluciones")
    columnas_existentes = [col for col in CONFIG["columnas_vista_detalle"] if col in df_filtrado.columns]
    
    if columnas_existentes:
        st.dataframe(
            df_filtrado[columnas_existentes],
            use_container_width=True,
            hide_index=True,
            height=400
        )
    else:
        st.dataframe(df_filtrado, use_container_width=True, height=400)

if __name__ == "__main__":
    main()
# app.py