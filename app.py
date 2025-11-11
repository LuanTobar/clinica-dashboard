import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import re

# Configuración de la página
st.set_page_config(
    page_title="Dashboard Reuniones Clínicas Dentales",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título principal
st.title("📊 Dashboard de Reuniones Clínicas Dentales")
st.markdown("---")

# Cargar datos
@st.cache_data
def load_data():
    df = pd.read_csv('data/clinicas.csv')
    
    # Limpieza de datos
    df['nombre_crm'] = df['nombre_crm'].str.strip()
    df['clinica'] = df['clinica'].str.strip()
    df['mes'] = df['mes'].str.lower().str.strip()
    
    # Convertir hora a formato datetime para mejor análisis
    df['Hora_dt'] = pd.to_datetime(df['Hora'], format='%H:%M:%S').dt.time
    df['Hora_num'] = pd.to_datetime(df['Hora'], format='%H:%M:%S').dt.hour
    
    # Ordenar meses cronológicamente
    meses_orden = {
        'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12, 'enero': 1
    }
    df['mes_num'] = df['mes'].map(meses_orden)
    df = df.sort_values('mes_num')
    
    return df

df = load_data()

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
    df_filtrado = df[df['mes'] == mes_seleccionado]
else:
    df_filtrado = df.copy()

# Botón de actualización
if st.sidebar.button("🔄 Actualizar Datos"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.info("📌 **Tip:** Haz clic en las barras para ver detalles")

# Layout principal
col1, col2 = st.columns([2, 1])

# Dashboard 1: Reuniones por Mes
with col1:
    st.header("📅 Reuniones por Mes")
    
    # Contar reuniones por mes
    reuniones_por_mes = df_filtrado.groupby('mes').agg({
        'nombre_crm': 'count',
        'clinica': list
    }).rename(columns={'nombre_crm': 'total_reuniones'}).reset_index()
    
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
    
    fig_meses.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(size=12),
        height=400
    )
    
    # Evento de clic en el gráfico
    selected_point = st.plotly_chart(fig_meses, use_container_width=True, on_select="rerun")
    
    # Mostrar detalles al seleccionar una barra
    if selected_point and selected_point.selection.points:
        punto = selected_point.selection.points[0]
        mes_seleccionado = punto['x']
        
        st.markdown(f"### 📋 Clínicas con reunión en **{mes_seleccionado.capitalize()}**")
        
        clinicas_mes = df[df['mes'] == mes_seleccionado][['nombre_crm', 'clinica', 'fecha', 'Hora', 'email_crm']]
        clinicas_mes = clinicas_mes.rename(columns={
            'nombre_crm': 'Nombre Contacto',
            'clinica': 'Clínica',
            'fecha': 'Fecha',
            'Hora': 'Hora',
            'email_crm': 'Email'
        })
        
        st.dataframe(
            clinicas_mes,
            use_container_width=True,
            hide_index=True
        )
        
        st.download_button(
            label="📥 Descargar lista como CSV",
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
    
    # Crear gráfico de barras horizontales
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
    
    fig_horas.update_layout(
        title="Reuniones por Franja Horaria",
        xaxis_title="Número de Reuniones",
        yaxis_title="Franja Horaria",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=400,
        margin=dict(l=100, r=50, t=80, b=50)
    )
    
    st.plotly_chart(fig_horas, use_container_width=True)
    
    # Mostrar estadísticas
    st.markdown("### 📊 Estadísticas")
    if not franjas.empty:
        franja_mas = franjas.idxmax()
        franja_menos = franjas.idxmin()
        
        st.metric("Franja con más reuniones", franja_mas)
        st.metric("Franja con menos reuniones", franja_menos)
        st.metric("Total reuniones", len(df_filtrado))

# Segunda fila con detalles adicionales
st.markdown("---")

# Resumen mensual detallado
if mes_seleccionado != "Todos los meses":
    st.header(f"📈 Detalles de {mes_seleccionado.capitalize()}")
    
    col3, col4 = st.columns(2)
    
    with col3:
        # Top clínicas por contacto (si hay múltiples)
        contactos_mes = df_filtrado['nombre_crm'].value_counts().head(5)
        if not contactos_mes.empty:
            st.subheader("👤 Top Contactos")
            for contacto, count in contactos_mes.items():
                st.write(f"- **{contacto}**: {count} reuniones")
    
    with col4:
        # Distribución por día del mes
        df_filtrado['dia'] = pd.to_datetime(df_filtrado['fecha'], format='%d/%m/%Y').dt.day
        dias_counts = df_filtrado['dia'].value_counts().sort_index()
        
        st.subheader("📆 Reuniones por Día")
        fig_dias = px.bar(
            x=dias_counts.index,
            y=dias_counts.values,
            labels={'x': 'Día del mes', 'y': 'Reuniones'},
            height=250
        )
        fig_dias.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=50, r=50, t=50, b=50)
        )
        st.plotly_chart(fig_dias, use_container_width=True)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center;'>
        <p>Dashboard generado con Streamlit | Última actualización: {}</p>
    </div>
    """.format(datetime.now().strftime("%d/%m/%Y %H:%M")),
    unsafe_allow_html=True
)