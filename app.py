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
    vars_x = conf.get('vars_x', [])
    vars_y = conf.get('vars_y', [])
    
    if not vars_x:
        return None
        
    df_calc = df.copy()
    funcion_agg = pd.Series.nunique if conf['funcion'] == 'Conteo Único' else 'count'
    
    # 1. MODO TABLA DINÁMICA
    if conf['tipo'] == 'Tabla Dinámica':
        pivot = pd.pivot_table(df_calc, values=conf['metrica'], 
                               index=vars_x, columns=vars_y if vars_y else None, 
                               aggfunc=funcion_agg, dropna=False)
        pivot = pivot.fillna(0)
        return pivot.reset_index()

    # 2. MODO GRÁFICOS
    group_vars = vars_x + vars_y
    # Agrupamos manteniendo los nulos para no perder data
    df_grp = df_calc.groupby(group_vars, dropna=False)[conf['metrica']].agg(funcion_agg).reset_index()
    df_grp = df_grp.rename(columns={conf['metrica']: 'Valor'})
    
    # --- ORDENAMIENTO NUMÉRICO ESTRUCTURAL ---
    # Ordenamos antes de convertir a texto. Los números se ordenan bien, los nulos van al final.
    df_grp = df_grp.sort_values(by=group_vars)

    # --- FORMATEO VISUAL PARA PLOTLY ---
    # Ahora sí pasamos a string y tapamos los nulos con una etiqueta para forzar el eje categórico
    for col in group_vars:
        df_grp[col] = df_grp[col].fillna("Sin Especificar").astype(str)
    
    eje_x = " - ".join(vars_x)
    if len(vars_x) > 1:
        df_grp[eje_x] = df_grp[vars_x].agg(' - '.join, axis=1)
    else:
        df_grp[eje_x] = df_grp[vars_x[0]]
        
    eje_color = " - ".join(vars_y) if vars_y else None
    if vars_y:
        if len(vars_y) > 1:
            df_grp[eje_color] = df_grp[vars_y].agg(' - '.join, axis=1)
        else:
            df_grp[eje_color] = df_grp[vars_y[0]]

    fig = None
    # Ya no hace falta re-ordenar el dataframe en las llamadas a px porque ya viene ordenado de arriba
    if conf['tipo'] in ['Barras', 'Barras Apiladas', 'Barras 100%']:
        fig = px.bar(df_grp, x=eje_x, y='Valor', color=eje_color, template="plotly_white")
        if conf['tipo'] == 'Barras Apiladas':
            fig.update_layout(barmode='stack')
        elif conf['tipo'] == 'Barras 100%':
            fig.update_layout(barmode='stack', barnorm='percent')
            fig.update_yaxes(title_text="Porcentaje (%)")
        else:
            fig.update_layout(barmode='group')
            
    elif conf['tipo'] == 'Líneas':
        fig = px.line(df_grp, x=eje_x, y='Valor', color=eje_color, markers=True, template="plotly_white")
        
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
        st.warning("Base de datos vacía. Ejecute el manager para cargar datos.")
        st.stop()

    st.sidebar.header("Modo")
    modo_vista = st.sidebar.radio("", ["Constructor", "Visor de Reportes"])
    st.sidebar.divider()
    
    st.sidebar.header("Filtros Globales")
    df_filtrado = df.copy()
    for col in CONFIG["columnas_filtro"]:
        if col in df.columns:
            # Rellenamos nulos temporalmente solo para armar la lista de opciones y buscar coincidencias
            opciones = sorted(df[col].fillna("Sin Especificar").astype(str).unique())
            seleccion = st.sidebar.multiselect(f"{col}:", opciones, default=[])
            if seleccion:
                df_filtrado = df_filtrado[df_filtrado[col].fillna("Sin Especificar").astype(str).isin(seleccion)]

    st.sidebar.markdown(f"**Registros:** {len(df_filtrado)}")

    if modo_vista == "Constructor":
        st.markdown("### Diseñar Visualización")
        
        exclusiones = ['CASO', 'CASO.1', 'SUMARIO', 'RUTA / REFERNCIA EN U', 'NOTAS']
        opciones_dims = [c for c in df.columns if c not in exclusiones]
        
        col1, col2, col3 = st.columns(3)
        vars_x = col1.multiselect("Filas (Eje Principal):", opciones_dims, default=[])
        vars_y = col2.multiselect("Columnas (Agrupación / Color):", opciones_dims, default=[])
        tipo_grafico = col3.selectbox("Formato Visual:", [
            "Tabla Dinámica", "Barras", "Barras Apiladas", "Barras 100%", "Líneas", "Dona"
        ])
        
        col_m1, col_m2, col_m3 = st.columns(3)
        metrica = col_m1.selectbox("Métrica:", [CONFIG["metrica_default"]] + opciones_dims)
        funcion = col_m2.selectbox("Operación:", ["Conteo Único", "Conteo Simple"])
        titulo_custom = col_m3.text_input("Título:", "Análisis Cruzado")

        if vars_x:
            conf_actual = {
                'titulo': titulo_custom, 'vars_x': vars_x, 'vars_y': vars_y,
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
                st.success("Visualización guardada.")

    elif modo_vista == "Visor de Reportes":
        st.markdown("### Reporte Consolidado")
        
        if not st.session_state['reportes_guardados']:
            st.info("No hay visualizaciones guardadas.")
        else:
            col_limpiar, col_export = st.columns([1, 4])
            if col_limpiar.button("Limpiar Reporte"):
                st.session_state['reportes_guardados'] = []
                st.rerun()

            elementos_para_exportar = []
            
            for conf in st.session_state['reportes_guardados']:
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