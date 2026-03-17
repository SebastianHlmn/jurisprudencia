# app.py
import os
import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px

from config import CONFIG
from export_utils import generar_word_dinamico

def inicializar_sesion():
    if 'reportes_guardados' not in st.session_state:
        # Guardaremos diccionarios de configuración, no figuras estáticas
        st.session_state['reportes_guardados'] = []

@st.cache_data(ttl=300)
def load_data_from_db(db_path, table_name):
    if not os.path.exists(db_path):
        return pd.DataFrame()
    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error de base de datos: {e}")
        return pd.DataFrame()

def motor_visualizacion(df, conf):
    """
    Toma un DataFrame y una configuración, calcula las agregaciones jerárquicas 
    y devuelve una figura de Plotly o un DataFrame (si es tipo Tabla).
    """
    vars_agrupacion = conf['vars_x'].copy()
    if conf['var_color'] and conf['var_color'] not in vars_agrupacion:
        vars_agrupacion.append(conf['var_color'])
        
    if not vars_agrupacion:
        return None
        
    # Lógica de cálculo (Count Distinct o Count)
    if conf['funcion'] == 'Conteo Único':
        df_grp = df.groupby(vars_agrupacion, dropna=False)[conf['metrica']].nunique().reset_index()
    else:
        df_grp = df.groupby(vars_agrupacion, dropna=False)[conf['metrica']].count().reset_index()
        
    df_grp = df_grp.rename(columns={conf['metrica']: 'Valor'})
    
    if conf['tipo'] == 'Tabla':
        return df_grp
        
    # Preparar eje X anidado para Plotly
    eje_x = conf['vars_x'][0]
    if len(conf['vars_x']) > 1:
        eje_x = " - ".join(conf['vars_x'])
        df_grp[eje_x] = df_grp[conf['vars_x']].astype(str).agg(' - '.join, axis=1)

    color_arg = conf['var_color'] if conf['var_color'] else None

    # Renderizado
    fig = None
    if conf['tipo'] == 'Barras':
        fig = px.bar(df_grp.sort_values('Valor', ascending=True), 
                     x='Valor', y=eje_x, color=color_arg, orientation='h', template="plotly_white")
    elif conf['tipo'] == 'Líneas':
        fig = px.line(df_grp.sort_values(eje_x), 
                      x=eje_x, y='Valor', color=color_arg, markers=True, template="plotly_white")
    elif conf['tipo'] == 'Dona':
        fig = px.pie(df_grp, names=eje_x, values='Valor', hole=0.4, template="plotly_white")
        
    if fig:
        fig.update_layout(title=conf['titulo'])
        
    return fig

def main():
    st.set_page_config(page_title=CONFIG["app_title"], layout="wide")
    inicializar_sesion()
    st.title(CONFIG["app_title"])
    
    df = load_data_from_db(CONFIG["db_path"], CONFIG["table_name"])
    if df.empty:
        st.warning("Base de datos vacía o no encontrada.")
        st.stop()

    # --- PANEL LATERAL ---
    st.sidebar.header("Modo de Trabajo")
    modo_vista = st.sidebar.radio("", ["Constructor", "Visor de Reportes"])
    st.sidebar.divider()
    
    st.sidebar.header("Filtros Globales")
    df_filtrado = df.copy()
    for col in CONFIG["columnas_filtro"]:
        if col in df.columns:
            opciones = sorted(df[col].dropna().astype(str).unique())
            seleccion = st.sidebar.multiselect(f"{col}:", opciones, default=[])
            if seleccion:
                df_filtrado = df_filtrado[df_filtrado[col].isin(seleccion)]

    st.markdown(f"**Volumen de datos actual:** {len(df_filtrado)} registros filtrados.")
    st.divider()

    # --- MODO CONSTRUCTOR ---
    if modo_vista == "Constructor":
        st.markdown("### Diseñar Visualización")
        
        exclusiones = ['CASO', 'CASO.1', 'SUMARIO', 'RUTA / REFERNCIA EN U', 'NOTAS']
        opciones_dims = [c for c in df.columns if c not in exclusiones]
        
        col1, col2, col3 = st.columns(3)
        vars_x = col1.multiselect("Jerarquía (Filas / Eje Principal):", opciones_dims, default=[])
        var_color = col2.selectbox("Subcategoría (Columnas / Color):", ["Ninguna"] + opciones_dims)
        var_color = None if var_color == "Ninguna" else var_color
        
        metrica = col3.selectbox("Métrica a evaluar:", [CONFIG["metrica_default"]] + opciones_dims)
        funcion = col1.selectbox("Operación:", ["Conteo Único", "Conteo Simple"])
        tipo_grafico = col2.selectbox("Formato:", ["Barras", "Líneas", "Dona", "Tabla"])
        titulo_custom = col3.text_input("Título de la visualización:", "Análisis de Datos")

        if vars_x:
            conf_actual = {
                'titulo': titulo_custom, 'vars_x': vars_x, 'var_color': var_color,
                'metrica': metrica, 'funcion': funcion, 'tipo': tipo_grafico
            }
            
            st.markdown("#### Vista Previa")
            elemento_previo = motor_visualizacion(df_filtrado, conf_actual)
            
            if isinstance(elemento_previo, pd.DataFrame):
                st.dataframe(elemento_previo, use_container_width=True, hide_index=True)
            elif elemento_previo is not None:
                st.plotly_chart(elemento_previo, use_container_width=True)
                
            if st.button("Guardar en el Visor de Reportes"):
                st.session_state['reportes_guardados'].append(conf_actual)
                st.success("Visualización guardada. Cambie al Visor para ver el reporte consolidado.")

    # --- MODO VISOR DE REPORTES ---
    elif modo_vista == "Visor de Reportes":
        st.markdown("### Reporte Consolidado")
        
        if not st.session_state['reportes_guardados']:
            st.info("No hay visualizaciones guardadas. Vaya al Constructor para crearlas.")
        else:
            col_limpiar, col_export = st.columns([1, 4])
            if col_limpiar.button("Limpiar Reporte"):
                st.session_state['reportes_guardados'] = []
                st.rerun()

            elementos_para_exportar = []
            cols_grid = st.columns(2)
            
            # Recalcular y dibujar cada configuración con los datos filtrados actuales
            for i, conf in enumerate(st.session_state['reportes_guardados']):
                st.markdown(f"#### {conf['titulo']}")
                elemento = motor_visualizacion(df_filtrado, conf)
                
                elementos_para_exportar.append((conf['titulo'], elemento))
                
                if isinstance(elemento, pd.DataFrame):
                    st.dataframe(elemento, use_container_width=True, hide_index=True)
                elif elemento is not None:
                    st.plotly_chart(elemento, use_container_width=True)
                    
            st.divider()
            if col_export.button("Generar Informe en Word"):
                with st.spinner("Compilando..."):
                    buffer = generar_word_dinamico(df_filtrado, elementos_para_exportar, CONFIG)
                    st.download_button("⬇️ Descargar Archivo", buffer, "Informe_Jurisprudencia.docx",
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document")

    st.divider()
    st.markdown("### Datos Base")
    cols_existentes = [c for c in CONFIG["columnas_vista_detalle"] if c in df_filtrado.columns]
    st.dataframe(df_filtrado[cols_existentes] if cols_existentes else df_filtrado, 
                 use_container_width=True, hide_index=True, height=300)

if __name__ == "__main__":
    main()
# app.py