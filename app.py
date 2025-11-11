import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Configuración de la página
st.set_page_config(
    page_title="Dashboard Reuniones Clínicas Dentales",
    page_icon="🦷",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título principal
st.title("📊 Dashboard de Reuniones Clínicas Dentales")
st.markdown("---")

# Cargar datos con manejo de errores
@st.cache_data(ttl=600)
def load_data():
    try:
        df = pd.read_csv('data/clinicas.csv')
        
        # Limpieza de datos
        df['nombre_crm'] = df['nombre_crm'].astype(str).str.strip()
        df['clinica'] = df['clinica'].astype(str).str.strip()
        df['mes'] = df['mes'].astype(str).str.lower().str.strip()
        
        # Convertir hora a formato numérico para análisis
        df['Hora_num'] = pd.to_datetime(df['Hora'], format='%H:%M:%S').dt.hour
        
        # Ordenar meses cronológicamente (2025 → 2026)
        meses_orden = {
            'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12, 'enero': 13
        }
        df['mes_num'] = df['mes'].map(meses_orden)
        df = df.sort_values('mes_num')
        
        return df
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return pd.DataFrame()

df = load_data()

# Verificar si hay datos
if df.empty:
    st.stop()

# Sidebar - Filtros
st.sidebar.header("🔧 Filtros Interactivos")

# Filtro de mes
meses_unicos = df['mes'].unique()
mes_seleccionado = st.sidebar.selectbox(
    "Seleccionar Mes",
    options=["Todos los meses"] + list(meses_unicos)
)

# Filtrar datos
if mes_seleccionado != "Todos los meses":
    df_filtrado = df[df['mes'] == mes_seleccionado].copy()
else:
    df_filtrado = df.copy()

# Botón de actualización
if st.sidebar.button("🔄 Actualizar Datos"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.info("📌 Haz clic en las barras para ver detalles")

# Layout principal
col1, col2 = st.columns([2, 1])

# Dashboard 1: Reuniones por Mes
with col1:
    st.header("📅 Reuniones por Mes")
    
    # Contar reuniones por mes
    reuniones_por_mes = df_filtrado.groupby('mes', as_index=False).size()
    reuniones_por_mes.columns = ['mes', 'total_reuniones']
    
    # Crear gráfico de barras interactivo
    fig_meses = px.bar(
        reuniones_por_mes,
        x='mes',
        y='total_reuniones',
        title="Total de Reuniones por Mes",
        labels={'mes': 'Mes', 'total_reuniones': 'Número de Reuniones'},
        color='total_reuniones',
        color_continuous_scale='Viridis',
        text_auto=True
    )
    fig_meses.update_layout(height=400)
    
    # Mostrar gráfico
    st.plotly_chart(fig_meses, use_container_width=True)
    
    # Mostrar detalles del mes seleccionado
    if mes_seleccionado != "Todos los meses":
        st.markdown(f"### 📋 Clínicas en **{mes_seleccionado.capitalize()}**")
        
        clinicas_mes = df[df['mes'] == mes_seleccionado][['nombre_crm', 'clinica', 'fecha', 'Hora', 'email_crm']]
        clinicas_mes.columns = ['Nombre Contacto', 'Clínica', 'Fecha', 'Hora', 'Email']
        
        st.dataframe(clinicas_mes, use_container_width=True, hide_index=True)
        
        st.download_button(
            label="📥 Descargar lista CSV",
            data=clinicas_mes.to_csv(index=False).encode('utf-8'),
            file_name=f'clinicas_{mes_seleccionado}.csv',
            mime='text/csv'
        )

# Dashboard 2: Análisis de Franjas Horarias
with col2:
    st.header("⏰ Franjas Horarias")
    
    # Crear franjas horarias
    bins = [8, 10, 12, 14, 16, 18, 20]
    labels = ['8-10', '10-12', '12-14', '14-16', '16-18', '18-20']
    
    df_filtrado['franja_horaria'] = pd.cut(df_filtrado['Hora_num'], bins=bins, labels=labels, right=False)
    franjas = df_filtrado['franja_horaria'].value_counts().sort_index()
    
    if not franjas.empty:
        fig_horas = go.Figure(data=[
            go.Bar(
                y=franjas.index,
                x=franjas.values,
                orientation='h',
                marker_color='rgba(55, 83, 109, 0.7)',
                text=franjas.values,
                textposition='outside'
            )
        ])
        fig_horas.update_layout(height=400, margin=dict(l=100, r=50, t=80, b=50))
        st.plotly_chart(fig_horas, use_container_width=True)
    
    # Estadísticas
    st.metric("Total reuniones", len(df_filtrado))

# Footer
st.markdown("---")
st.caption(f"🔄 Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
