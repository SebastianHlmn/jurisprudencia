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
        
        for col in df.columns:
            if pd.api.types.is_float_dtype(df[col]):
                s_dropna = df[col].dropna()
                if not s_dropna.empty and s_dropna.apply(float.is_integer).all():
                    df[col] = df[col].astype('Int64')
                    
        return df
    except Exception as e:
        st.error(f"Error de base de datos: {e}")
        return pd.DataFrame()

def motor_visualizacion(df, conf):
    vars_x = conf.get('vars_x', [])
    vars_y = [y for y in conf.get('vars_y', []) if y not in vars_x]
    
    if not vars_x:
        return None
        
    df_calc = df.copy()
    funcion_agg = pd.Series.nunique if conf['funcion'] == 'Conteo Único' else 'count'
    
    def limpiar_decimales_cero(texto):
        txt = str(texto)
        if txt.endswith('.0') and txt[:-2].replace('-', '').isdigit():
            return txt[:-2]
        return txt

    # 1. MODO TABLA DINÁMICA
    if conf['tipo'] == 'Tabla Dinámica':
        pivot = pd.pivot_table(df_calc, values=conf['metrica'], 
                               index=vars_x, columns=vars_y if vars_y else None, 
                               aggfunc=funcion_agg, dropna=False,
                               margins=conf.get('totales', False),
                               margins_name='Total General')
        pivot = pivot.fillna(0)
        pivot = pivot.reset_index()
        
        # Limpiar nombres de columnas
        pivot.columns = [limpiar_decimales_cero(col) if not isinstance(col, tuple) else " - ".join(map(limpiar_decimales_cero, col)) for col in pivot.columns]
        
        # Re-convertir los valores de la tabla a Int64 para la UI web
        for col in pivot.columns:
            if pd.api.types.is_float_dtype(pivot[col]):
                s_dropna = pivot[col].dropna()
                if not s_dropna.empty and s_dropna.apply(float.is_integer).all():
                    pivot[col] = pivot[col].astype('Int64')
                    
        return pivot

    # 2. MODO GRÁFICOS
    group_vars = vars_x + vars_y
    df_grp = df_calc.groupby(group_vars, dropna=False)[conf['metrica']].agg(funcion_agg).reset_index()
    df_grp = df_grp.rename(columns={conf['metrica']: 'Valor'})
    
    df_grp = df_grp.sort_values(by=group_vars)

    for col in group_vars:
        df_grp[col] = df_grp[col].astype(str).replace({"<NA>": "Sin Especificar", "nan": "Sin Especificar", "None": "Sin Especificar"})
    
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

def mostrar_elemento_ui(elemento, conf):
    if isinstance(elemento, pd.DataFrame):
        col_x = conf['vars_x'][0]
        if conf.get('totales', False) and col_x in elemento.columns:
            mask_total = elemento[col_x] == 'Total General'
            
            st.dataframe(elemento[~mask_total], use_container_width=True, hide_index=True)
            
            if mask_total.any():
                st.caption("Totales Generales (Congelados)")
                st.dataframe(elemento[mask_total], use_container_width=True, hide_index=True)
        else:
            st.dataframe(elemento, use_container_width=True, hide_index=True)
            
    elif elemento is not None:
        st.plotly_chart(elemento, use_container_width=True)

def main():
    st.set_page_config(page_title=CONFIG["app_title"], layout="wide")
    inicializar_sesion()
    st.title(CONFIG["app_title"])
    
    df = load_data_from_db(CONFIG["db_path"], CONFIG["table_name"])
    if df.empty:
        st.warning("Base de datos vacía. Ejecute el manager para cargar datos.")
        st.stop()

    st.sidebar.header("Modo")
    modo_vista = st.sidebar.radio("Navegación", ["Constructor", "Visor de Reportes"], label_visibility="collapsed")
    st.sidebar.divider()
    
    st.sidebar.header("Filtros Globales")
    
    exclusiones_filtros = ['CASO', 'CASO.1', 'SUMARIO', 'RUTA / REFERNCIA EN U', 'NOTAS']
    columnas_filtrables = [c for c in df.columns if c not in exclusiones_filtros]
    filtros_por_defecto = [c for c in CONFIG.get("columnas_filtro", []) if c in columnas_filtrables]
    
    variables_a_filtrar = st.sidebar.multiselect(
        "Agregar variables de filtro:", 
        columnas_filtrables, 
        default=filtros_por_defecto
    )
    
    df_filtrado = df.copy()
    
    for col in variables_a_filtrar:
        serie_str = df[col].astype(str).replace({"<NA>": "Sin Especificar", "nan": "Sin Especificar", "None": "Sin Especificar"})
        opciones = sorted(serie_str.unique())
        seleccion = st.sidebar.multiselect(f"{col}:", opciones, default=[])
        
        if seleccion:
            serie_filtro = df_filtrado[col].astype(str).replace({"<NA>": "Sin Especificar", "nan": "Sin Especificar", "None": "Sin Especificar"})
            df_filtrado = df_filtrado[serie_filtro.isin(seleccion)]

    st.sidebar.markdown(f"**Registros analizados:** {len(df_filtrado)}")

    if modo_vista == "Constructor":
        st.markdown("### Diseñar Visualización")
        
        exclusiones_dims = ['CASO', 'CASO.1', 'SUMARIO', 'RUTA / REFERNCIA EN U', 'NOTAS']
        opciones_dims = [c for c in df.columns if c not in exclusiones_dims]
        
        col1, col2, col3 = st.columns(3)
        vars_x = col1.multiselect("Filas (Eje Principal):", opciones_dims, default=[])
        
        opciones_dims_y = [c for c in opciones_dims if c not in vars_x]
        vars_y = col2.multiselect("Columnas (Agrupación / Color):", opciones_dims_y, default=[])
        
        tipo_grafico = col3.selectbox("Formato Visual:", [
            "Tabla Dinámica", "Barras", "Barras Apiladas", "Barras 100%", "Líneas", "Dona"
        ])
        
        col_m1, col_m2, col_m3 = st.columns(3)
        metrica = col_m1.selectbox("Métrica:", [CONFIG["metrica_default"]] + opciones_dims)
        funcion = col_m2.selectbox("Operación:", ["Conteo Único", "Conteo Simple"])
        titulo_custom = col_m3.text_input("Título:", "Análisis Cruzado")

        mostrar_totales = False
        if tipo_grafico == "Tabla Dinámica":
            mostrar_totales = st.checkbox("Incluir Totales en Filas y Columnas", value=False)

        if vars_x:
            conf_actual = {
                'titulo': titulo_custom, 'vars_x': vars_x, 'vars_y': vars_y,
                'metrica': metrica, 'funcion': funcion, 'tipo': tipo_grafico,
                'totales': mostrar_totales
            }
            
            st.markdown("#### Vista Previa")
            elemento_previo = motor_visualizacion(df_filtrado, conf_actual)
            mostrar_elemento_ui(elemento_previo, conf_actual)
                
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
                mostrar_elemento_ui(elemento, conf)
                    
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