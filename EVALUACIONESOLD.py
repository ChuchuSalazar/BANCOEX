import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import seaborn as sns
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import warnings
warnings.filterwarnings('ignore')

#adaptacion movil
# Al inicio del archivo, después de las importaciones
# Configuración responsiva mejorada
st.set_page_config(
    page_title="Análisis de Evaluación de Desempeño",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="auto"  # Cambiar de "expanded" a "auto"
)

# CSS personalizado para móvil
def inject_mobile_css():
    st.markdown("""
    <style>
    /* Ajustes para móviles */
    @media (max-width: 768px) {
        .main .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
            padding-top: 1rem;
        }
        
        /* Hacer gráficos más pequeños en móvil */
        .plotly-graph-div {
            height: 400px !important;
        }
        
        /* Ajustar métricas para móvil */
        div[data-testid="metric-container"] {
            background-color: #f0f2f6;
            border: 1px solid #d6d6d6;
            padding: 5px 10px;
            border-radius: 5px;
            margin: 2px;
        }
        
        /* Sidebar más estrecho en móvil */
        .css-1d391kg {
            width: 250px;
        }
        
        /* Tablas responsivas */
        .dataframe {
            font-size: 12px;
        }
    }
    
    /* Ajustes para tablets */
    @media (max-width: 1024px) and (min-width: 769px) {
        .plotly-graph-div {
            height: 500px !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)


def is_mobile_device():
    """Detecta si el usuario está en un dispositivo móvil"""
    # Streamlit no tiene acceso directo al user agent, pero podemos usar la resolución
    # Como aproximación, usamos el ancho de la ventana del navegador
    return st.session_state.get('mobile_detected', False)

def setup_device_detection():
    """Configura la detección de dispositivo"""
    # JavaScript para detectar dispositivo móvil
    device_detection = """
    <script>
    function detectMobile() {
        return window.innerWidth <= 768;
    }
    
    if (detectMobile()) {
        window.parent.postMessage({type: 'mobile_detected', value: true}, '*');
    }
    </script>
    """
    st.components.v1.html(device_detection, height=0)
def create_mobile_friendly_3d_scatter(df, is_mobile=False):
    """Versión optimizada para móvil del gráfico 3D"""
    
    if is_mobile:
        # En móvil, usar gráfico 2D más simple
        unit_summary = df.groupby(['UNIDAD_ORGANIZATIVA', 'BANDA_DESEMPEÑO']).size().reset_index(name='Cantidad')
        
        fig = px.bar(
            unit_summary,
            x='BANDA_DESEMPEÑO',
            y='Cantidad',
            color='UNIDAD_ORGANIZATIVA',
            title="Distribución por Bandas de Desempeño (Vista Móvil)",
            height=400
        )
        
        fig.update_layout(
            xaxis_tickangle=45,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
    else:
        # Gráfico 3D original para desktop
        fig = create_3d_scatter_by_unit(df)
        
    return fig

def create_mobile_dashboard_metrics(df):
    """Métricas optimizadas para móvil"""
    
    # En móvil, mostrar métricas en 2 columnas en lugar de 4
    if st.session_state.get('mobile_detected', False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total Evaluados", len(df))
            excepcional = len(df[df['EVALUACION'].str.contains('Excepcional', na=False)])
            st.metric("Desempeño Excepcional", f"{excepcional}")
        
        with col2:
            avg_score = df['RESULTADO_CUANTITATIVO'].mean()
            st.metric("Puntuación Promedio", f"{avg_score:.1f}")
            avg_days = df['DIAS_A_PAGAR'].mean()
            st.metric("Días Promedio Bono", f"{avg_days:.0f}")
    else:
        # Layout original para desktop
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Evaluados", len(df), delta="293 empleados")
        with col2:
            avg_score = df['RESULTADO_CUANTITATIVO'].mean()
            st.metric("Puntuación Promedio", f"{avg_score:.1f}", 
                     delta=f"{avg_score - 350:.1f} vs esperado")
        with col3:
            excepcional = len(df[df['EVALUACION'].str.contains('Excepcional', na=False)])
            st.metric("Desempeño Excepcional", f"{excepcional}", 
                     delta=f"{(excepcional/len(df)*100):.1f}%")
        with col4:
            avg_days = df['DIAS_A_PAGAR'].mean()
            st.metric("Días Promedio Bono", f"{avg_days:.0f}", delta="días")
        # Configuración de la página
        st.set_page_config(
            page_title="Análisis de Evaluación de Desempeño",
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="expanded"
)

# Función para cargar y procesar los datos
@st.cache_data
def load_and_process_data():
    try:
        # Intentar cargar el archivo Excel
        file_path = r"C:\12 bancoex\evaluaciones\NOMINA DE EVALUACION III .xls"
        
        # Leer el archivo Excel
        df = pd.read_excel(file_path)
        
        # Limpiar nombres de columnas (remover espacios extra y caracteres especiales)
        df.columns = df.columns.str.strip()
        
        # Mapear las columnas al formato esperado
        column_mapping = {
            'N°': 'NUMERO',
            'CÉDULA DE IDENTIDAD': 'CEDULA',
            'APELLIDOS Y NOMBRE': 'NOMBRE',
            'ÁREA DE PERSONAL': 'AREA_PERSONAL',
            'FECHA DE INGRESO': 'FECHA_INGRESO',
            'UNIDAD ORGANIZATIVA': 'UNIDAD_ORGANIZATIVA',
            'CARGO': 'CARGO',
            'RESULTADO CUANTITATIVO': 'RESULTADO_CUANTITATIVO',
            'RESULTADO \nEVALUACIÓN 3ER TRIMESTRE AÑO 2025': 'EVALUACION',
            'DIAS A PAGAR': 'DIAS_A_PAGAR'
        }
        
        # Renombrar columnas
        for old_col, new_col in column_mapping.items():
            if old_col in df.columns:
                df = df.rename(columns={old_col: new_col})
        
        # Limpiar y procesar los datos
        # Convertir RESULTADO_CUANTITATIVO a numérico
        df['RESULTADO_CUANTITATIVO'] = pd.to_numeric(df['RESULTADO_CUANTITATIVO'], errors='coerce')
        
        # Convertir DIAS_A_PAGAR a numérico
        df['DIAS_A_PAGAR'] = pd.to_numeric(df['DIAS_A_PAGAR'], errors='coerce')
        
        # Procesar fechas
        if 'FECHA_INGRESO' in df.columns:
            df['FECHA_INGRESO'] = pd.to_datetime(df['FECHA_INGRESO'], errors='coerce')
            # Calcular antigüedad en años
            df['ANTIGUEDAD_AÑOS'] = (datetime.now() - df['FECHA_INGRESO']).dt.days / 365.25
        else:
            df['ANTIGUEDAD_AÑOS'] = 0
        
        # Limpiar datos de evaluación
        if 'EVALUACION' in df.columns:
            # Normalizar las evaluaciones
            df['EVALUACION'] = df['EVALUACION'].str.strip()
            
            # Mapear evaluaciones inconsistentes
            eval_mapping = {
                'Sobre Lo Esperado': 'Sobre Lo Esperado',
                'Sobresaliente / Excepcional': 'Sobresaliente / Excepcional',
                'Dentro lo esperado': 'Dentro lo esperado',
                'Por debajo de lo Esperado': 'Por debajo de lo Esperado',
                'Debajo lo esperado': 'Por debajo de lo Esperado',
                'Muy por debajo de lo esperado': 'Muy por debajo de lo esperado'
            }
            
            df['EVALUACION'] = df['EVALUACION'].map(eval_mapping).fillna(df['EVALUACION'])
        
        # Eliminar filas vacías
        df = df.dropna(subset=['RESULTADO_CUANTITATIVO'])
        
        # Validar que tenemos las columnas necesarias
        required_columns = ['RESULTADO_CUANTITATIVO', 'EVALUACION', 'DIAS_A_PAGAR']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            st.error(f"Faltan las siguientes columnas en el archivo: {missing_columns}")
            st.stop()
        
        # Mostrar información de carga
        st.success(f"✅ Archivo cargado exitosamente: {len(df)} registros procesados")
        
        return df
        
    except FileNotFoundError:
        st.error(f"❌ No se encontró el archivo en la ruta: {file_path}")
        st.info("📋 Usando datos de ejemplo para la demostración")
        
        # Datos de ejemplo basados en tu estructura
        data_sample = [
            [1, 16543494, "Lara Toro, Guillermo Gabriel", "Alta Gerencia", "16/11/2020", "Presidencia", "Presidente", 417, "Sobre Lo Esperado", 40],
            [2, 5424330, "Figueroa Tovar, Alfredo Enrique", "Contratados (Jubilado)", "26/4/2021", "Coordinación de Riesgo de Mercado y Liquidez", "Especialista IV", 445, "Sobresaliente / Excepcional", 50],
            [3, 5963047, "Morales Vaamonde, Marlene Cecilia", "Contratados (Jubilado)", "15/6/2021", "Coordinación de Contratos y Asesoría Legal", "Coordinador (E)", 426, "Sobresaliente / Excepcional", 50],
            [4, 6182193, "Cardenas Pernia, Tommy Alex", "Contratados (Jubilado)", "10/6/2021", "Gerencia de Tecnología de la Información", "Gerente (E)", 357, "Sobre Lo Esperado", 40],
            [5, 25987538, "Meza Mujica, Karem Cecilia", "Contratados", "2/5/2022", "Gerencia de Estudios Económicos", "Especialista I", 417, "Sobre Lo Esperado", 40]
        ]
        
        df = pd.DataFrame(data_sample, columns=[
            'NUMERO', 'CEDULA', 'NOMBRE', 'AREA_PERSONAL', 'FECHA_INGRESO', 
            'UNIDAD_ORGANIZATIVA', 'CARGO', 'RESULTADO_CUANTITATIVO', 'EVALUACION', 'DIAS_A_PAGAR'
        ])
        
        # Procesar fechas en datos de ejemplo
        df['FECHA_INGRESO'] = pd.to_datetime(df['FECHA_INGRESO'], format='%d/%m/%Y')
        df['ANTIGUEDAD_AÑOS'] = (datetime.now() - df['FECHA_INGRESO']).dt.days / 365.25
        
        return df
        
    except Exception as e:
        st.error(f"❌ Error al cargar el archivo: {str(e)}")
        st.info("Verifique que el archivo esté cerrado y en el formato correcto")
        st.stop()

# Función para crear gráfico 3D de distribución por área
def create_3d_area_performance(df):
    # Preparar datos para el gráfico 3D
    area_performance = df.groupby(['AREA_PERSONAL', 'EVALUACION']).agg({
        'RESULTADO_CUANTITATIVO': ['count', 'mean'],
        'DIAS_A_PAGAR': 'mean'
    }).round(2)
    
    area_performance.columns = ['Cantidad', 'Puntuacion_Promedio', 'Dias_Promedio']
    area_performance = area_performance.reset_index()
    
    fig = px.scatter_3d(
        area_performance,
        x='AREA_PERSONAL',
        y='EVALUACION',
        z='Puntuacion_Promedio',
        size='Cantidad',
        color='Dias_Promedio',
        hover_data=['Cantidad'],
        title="Distribución 3D: Área vs Evaluación vs Puntuación Promedio",
        color_continuous_scale='Viridis'
    )
    
    fig.update_layout(
        scene=dict(
            xaxis_title="Área de Personal",
            yaxis_title="Evaluación",
            zaxis_title="Puntuación Promedio"
        ),
        height=600
    )
    
    return fig

# Función para crear gráfico 3D de superficie de rendimiento
def create_3d_performance_surface(df):
    # Crear una superficie 3D basada en antigüedad y puntuación
    fig = go.Figure()
    
    # Preparar datos
    for area in df['AREA_PERSONAL'].unique():
        area_data = df[df['AREA_PERSONAL'] == area]
        
        fig.add_trace(go.Scatter3d(
            x=area_data['ANTIGUEDAD_AÑOS'],
            y=area_data['RESULTADO_CUANTITATIVO'],
            z=area_data['DIAS_A_PAGAR'],
            mode='markers',
            marker=dict(
                size=5,
                opacity=0.6
            ),
            name=area,
            text=area_data['EVALUACION'],
            hovertemplate="<b>%{text}</b><br>" +
                         "Antigüedad: %{x:.1f} años<br>" +
                         "Puntuación: %{y}<br>" +
                         "Días a pagar: %{z}<br>" +
                         "<extra></extra>"
        ))
    
    fig.update_layout(
        title="Superficie 3D: Antigüedad vs Puntuación vs Días a Pagar",
        scene=dict(
            xaxis_title="Antigüedad (años)",
            yaxis_title="Puntuación",
            zaxis_title="Días a Pagar"
        ),
        height=600
    )
    
    return fig

# Función para análisis descriptivo
def descriptive_analysis(df):
    st.subheader("📈 Análisis Descriptivo")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Empleados", len(df))
    with col2:
        st.metric("Puntuación Promedio", f"{df['RESULTADO_CUANTITATIVO'].mean():.1f}")
    with col3:
        st.metric("Días Promedio a Pagar", f"{df['DIAS_A_PAGAR'].mean():.1f}")
    with col4:
        st.metric("Antigüedad Promedio", f"{df['ANTIGUEDAD_AÑOS'].mean():.1f} años")
    
    # Distribución por evaluación
    st.subheader("Distribución por Nivel de Evaluación")
    eval_dist = df['EVALUACION'].value_counts()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.dataframe(eval_dist.to_frame("Cantidad"))
    
    with col2:
        fig_pie = px.pie(
            values=eval_dist.values,
            names=eval_dist.index,
            title="Distribución Porcentual de Evaluaciones"
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    return {
        'total_empleados': len(df),
        'puntuacion_promedio': df['RESULTADO_CUANTITATIVO'].mean(),
        'dias_promedio': df['DIAS_A_PAGAR'].mean(),
        'antiguedad_promedio': df['ANTIGUEDAD_AÑOS'].mean(),
        'distribucion_evaluacion': eval_dist.to_dict()
    }

# Función para crear histograma de distribución
def create_distribution_histogram(df):
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=("Distribución de Puntuaciones", "Distribución de Días a Pagar",
                       "Distribución por Área", "Distribución de Antigüedad"),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # Histograma de puntuaciones
    fig.add_trace(
        go.Histogram(x=df['RESULTADO_CUANTITATIVO'], nbinsx=30, name="Puntuaciones"),
        row=1, col=1
    )
    
    # Histograma de días a pagar
    fig.add_trace(
        go.Histogram(x=df['DIAS_A_PAGAR'], nbinsx=10, name="Días a Pagar"),
        row=1, col=2
    )
    
    # Distribución por área
    area_counts = df['AREA_PERSONAL'].value_counts()
    fig.add_trace(
        go.Bar(x=area_counts.index, y=area_counts.values, name="Por Área"),
        row=2, col=1
    )
    
    # Histograma de antigüedad
    fig.add_trace(
        go.Histogram(x=df['ANTIGUEDAD_AÑOS'], nbinsx=20, name="Antigüedad"),
        row=2, col=2
    )
    
    fig.update_layout(height=800, title_text="Análisis de Distribuciones")
    return fig

# Función para exportar a Excel
def export_to_excel(df, analysis_results):
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Datos principales
        df.to_excel(writer, sheet_name='Datos_Principales', index=False)
        
        # Resumen estadístico
        summary_stats = df[['RESULTADO_CUANTITATIVO', 'DIAS_A_PAGAR', 'ANTIGUEDAD_AÑOS']].describe()
        summary_stats.to_excel(writer, sheet_name='Estadisticas_Descriptivas')
        
        # Distribución por evaluación
        eval_dist = pd.DataFrame.from_dict(analysis_results['distribucion_evaluacion'], 
                                         orient='index', columns=['Cantidad'])
        eval_dist.to_excel(writer, sheet_name='Distribucion_Evaluacion')
        
        # Análisis por área
        area_analysis = df.groupby('AREA_PERSONAL').agg({
            'RESULTADO_CUANTITATIVO': ['count', 'mean', 'std'],
            'DIAS_A_PAGAR': 'mean',
            'ANTIGUEDAD_AÑOS': 'mean'
        }).round(2)
        area_analysis.to_excel(writer, sheet_name='Analisis_por_Area')
    
    output.seek(0)
    return output

# Función para generar PDF
def generate_pdf_report(df, analysis_results):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Título
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1  # Center
    )
    
    story.append(Paragraph("REPORTE DE ANÁLISIS DE EVALUACIÓN DE DESEMPEÑO", title_style))
    story.append(Paragraph(f"Fecha de Generación: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Resumen ejecutivo
    story.append(Paragraph("RESUMEN EJECUTIVO", styles['Heading2']))
    story.append(Paragraph(f"Total de Empleados Evaluados: {analysis_results['total_empleados']}", styles['Normal']))
    story.append(Paragraph(f"Puntuación Promedio: {analysis_results['puntuacion_promedio']:.2f}", styles['Normal']))
    story.append(Paragraph(f"Días Promedio a Pagar: {analysis_results['dias_promedio']:.1f}", styles['Normal']))
    story.append(Paragraph(f"Antigüedad Promedio: {analysis_results['antiguedad_promedio']:.1f} años", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Distribución de evaluaciones
    story.append(Paragraph("DISTRIBUCIÓN DE EVALUACIONES", styles['Heading2']))
    for eval_type, count in analysis_results['distribucion_evaluacion'].items():
        percentage = (count / analysis_results['total_empleados']) * 100
        story.append(Paragraph(f"• {eval_type}: {count} empleados ({percentage:.1f}%)", styles['Normal']))
    
    story.append(Spacer(1, 20))
    
    # Pie de página
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        alignment=1
    )
    story.append(Spacer(1, 50))
    story.append(Paragraph("Desarrollado por MSC. Jesús F. Salazar Rojas / Bajo Python ® / Septiembre 2025", footer_style))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# Función adicional para subir archivo manualmente
def load_file_uploader():
    """Permite al usuario subir su propio archivo Excel"""
    uploaded_file = st.sidebar.file_uploader(
        "📁 Subir archivo Excel alternativo", 
        type=['xls', 'xlsx'],
        help="Si el archivo no se encuentra en la ruta por defecto, puede subirlo aquí"
    )
    
    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
            
            # Aplicar el mismo procesamiento que en load_and_process_data
            df.columns = df.columns.str.strip()
            
            column_mapping = {
                'N°': 'NUMERO',
                'CÉDULA DE IDENTIDAD': 'CEDULA',
                'APELLIDOS Y NOMBRE': 'NOMBRE',
                'ÁREA DE PERSONAL': 'AREA_PERSONAL',
                'FECHA DE INGRESO': 'FECHA_INGRESO',
                'UNIDAD ORGANIZATIVA': 'UNIDAD_ORGANIZATIVA',
                'CARGO': 'CARGO',
                'RESULTADO CUANTITATIVO': 'RESULTADO_CUANTITATIVO',
                'RESULTADO \nEVALUACIÓN 3ER TRIMESTRE AÑO 2025': 'EVALUACION',
                'DIAS A PAGAR': 'DIAS_A_PAGAR'
            }
            
            for old_col, new_col in column_mapping.items():
                if old_col in df.columns:
                    df = df.rename(columns={old_col: new_col})
            
            df['RESULTADO_CUANTITATIVO'] = pd.to_numeric(df['RESULTADO_CUANTITATIVO'], errors='coerce')
            df['DIAS_A_PAGAR'] = pd.to_numeric(df['DIAS_A_PAGAR'], errors='coerce')
            
            if 'FECHA_INGRESO' in df.columns:
                df['FECHA_INGRESO'] = pd.to_datetime(df['FECHA_INGRESO'], errors='coerce')
                df['ANTIGUEDAD_AÑOS'] = (datetime.now() - df['FECHA_INGRESO']).dt.days / 365.25
            else:
                df['ANTIGUEDAD_AÑOS'] = 0
            
            df = df.dropna(subset=['RESULTADO_CUANTITATIVO'])
            
            st.sidebar.success(f"✅ Archivo subido: {len(df)} registros")
            return df
            
        except Exception as e:
            st.sidebar.error(f"Error al procesar archivo: {str(e)}")
            return None
    
    return None

# Función para obtener distribución esperada
def get_expected_distribution():
    """Solicita al usuario las cuotas esperadas por banda"""
    st.subheader("⚙️ Configuración de Cuotas Esperadas por Banda")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Defina el porcentaje esperado para cada banda:**")
        banda_100_179 = st.number_input("Muy por debajo (100-179):", min_value=0.0, max_value=100.0, value=5.0, step=0.1)
        banda_180_259 = st.number_input("Por debajo (180-259):", min_value=0.0, max_value=100.0, value=10.0, step=0.1)
        banda_260_339 = st.number_input("Dentro esperado (260-339):", min_value=0.0, max_value=100.0, value=25.0, step=0.1)
        banda_340_419 = st.number_input("Sobre esperado (340-419):", min_value=0.0, max_value=100.0, value=40.0, step=0.1)
        banda_420_500 = st.number_input("Excepcional (420-500):", min_value=0.0, max_value=100.0, value=20.0, step=0.1)
    
    with col2:
        total = banda_100_179 + banda_180_259 + banda_260_339 + banda_340_419 + banda_420_500
        
        if total == 100.0:
            st.success(f"✅ Total: {total}%")
        else:
            st.error(f"❌ Total: {total}% (debe sumar 100%)")
        
        # Gráfico de las cuotas esperadas
        expected_data = {
            'Muy por debajo': banda_100_179,
            'Por debajo': banda_180_259,
            'Dentro esperado': banda_260_339,
            'Sobre esperado': banda_340_419,
            'Excepcional': banda_420_500
        }
        
        fig_expected = px.pie(
            values=list(expected_data.values()),
            names=list(expected_data.keys()),
            title="Distribución Esperada"
        )
        st.plotly_chart(fig_expected, use_container_width=True)
    
    return {
        'muy_por_debajo': banda_100_179,
        'por_debajo': banda_180_259,
        'dentro_esperado': banda_260_339,
        'sobre_esperado': banda_340_419,
        'excepcional': banda_420_500
    } if total == 100.0 else None

# Función para crear bandas de desempeño
def create_performance_bands(df):
    """Crea las bandas de evaluación según los rangos cuantitativos"""
    
    # Limpiar datos primero
    df = clean_dataframe_for_analysis(df)
    
    def get_band(score):
        # Manejar casos de NaN
        if pd.isna(score):
            return "Sin evaluación"
        
        if 100 <= score <= 179:
            return "Muy por debajo (100-179)"
        elif 180 <= score <= 259:
            return "Por debajo (180-259)"
        elif 260 <= score <= 339:
            return "Dentro esperado (260-339)"
        elif 340 <= score <= 419:
            return "Sobre esperado (340-419)"
        elif 420 <= score <= 500:
            return "Excepcional (420-500)"
        else:
            return "Fuera de rango"
    
    df['BANDA_DESEMPEÑO'] = df['RESULTADO_CUANTITATIVO'].apply(get_band)
    return df

def create_3d_scatter_by_unit(df):
    """Gráfico 3D de dispersión por unidad organizativa y banda"""
    
    # Limpiar datos primero
    df = clean_dataframe_for_analysis(df)

    # Preparar datos
    unit_band_summary = df.groupby(['UNIDAD_ORGANIZATIVA', 'BANDA_DESEMPEÑO']).agg({
        'RESULTADO_CUANTITATIVO': ['count', 'mean'],
        'DIAS_A_PAGAR': 'mean'
    }).reset_index()
    
    unit_band_summary.columns = ['Unidad', 'Banda', 'Cantidad', 'Puntuacion_Promedio', 'Dias_Promedio']

    # SOLUCIÓN: Limpiar NaN
    unit_band_summary['Cantidad'] = unit_band_summary['Cantidad'].fillna(1)
    unit_band_summary['Puntuacion_Promedio'] = unit_band_summary['Puntuacion_Promedio'].fillna(0)
    unit_band_summary['Dias_Promedio'] = unit_band_summary['Dias_Promedio'].fillna(0)

    
    # Crear colores por banda
    color_map = {
        'Muy por debajo (100-179)': '#FF0000',
        'Por debajo (180-259)': '#FF6600',
        'Dentro esperado (260-339)': '#FFFF00',
        'Sobre esperado (340-419)': '#00FF00',
        'Excepcional (420-500)': '#0066FF'
    }
    
    fig = go.Figure()
    
    for banda in unit_band_summary['Banda'].unique():
        banda_data = unit_band_summary[unit_band_summary['Banda'] == banda]
        
        fig.add_trace(go.Scatter3d(
            x=banda_data['Unidad'],
            y=banda_data['Puntuacion_Promedio'],
            z=banda_data['Cantidad'],
            mode='markers',
            marker=dict(
                size=banda_data['Cantidad'] * 2,
                color=color_map.get(banda, '#808080'),
                opacity=0.8
            ),
            name=banda,
            text=banda_data.apply(lambda row: f"Unidad: {row['Unidad']}<br>Banda: {row['Banda']}<br>Empleados: {row['Cantidad']}<br>Puntuación: {row['Puntuacion_Promedio']:.1f}", axis=1),
            hovertemplate="%{text}<extra></extra>"
        ))
    
    fig.update_layout(
        title="Distribución 3D: Unidades Organizativas por Bandas de Desempeño",
        scene=dict(
            xaxis_title="Unidad Organizativa",
            yaxis_title="Puntuación Promedio",
            zaxis_title="Cantidad de Empleados"
        ),
        height=700
    )
    
    return fig


def create_real_vs_expected_analysis(df, expected_dist):
    """Análisis comparativo real vs esperado por unidad organizativa"""
    
    # Calcular distribución real
    real_dist = df['BANDA_DESEMPEÑO'].value_counts(normalize=True) * 100
    
    # Crear DataFrame comparativo
    comparison_data = []
    band_mapping = {
        'Muy por debajo (100-179)': 'muy_por_debajo',
        'Por debajo (180-259)': 'por_debajo',
        'Dentro esperado (260-339)': 'dentro_esperado',
        'Sobre esperado (340-419)': 'sobre_esperado',
        'Excepcional (420-500)': 'excepcional'
    }
    
    for banda_display, banda_key in band_mapping.items():
        real_pct = real_dist.get(banda_display, 0)
        expected_pct = expected_dist[banda_key]
        variance = real_pct - expected_pct
        
        comparison_data.append({
            'Banda': banda_display,
            'Real (%)': real_pct,
            'Esperado (%)': expected_pct,
            'Varianza (%)': variance,
            'Status': '🔴 Por debajo' if variance < -2 else '🟡 En rango' if abs(variance) <= 2 else '🟢 Por encima'
        })
    
    comparison_df = pd.DataFrame(comparison_data)
    
    # Gráfico de barras comparativo
    fig_comparison = go.Figure()
    
    fig_comparison.add_trace(go.Bar(
        name='Real',
        x=comparison_df['Banda'],
        y=comparison_df['Real (%)'],
        marker_color='lightblue'
    ))
    
    fig_comparison.add_trace(go.Bar(
        name='Esperado',
        x=comparison_df['Banda'],
        y=comparison_df['Esperado (%)'],
        marker_color='orange'
    ))
    
    fig_comparison.update_layout(
        title='Comparativo Real vs Esperado por Banda de Desempeño',
        xaxis_title='Banda de Desempeño',
        yaxis_title='Porcentaje (%)',
        barmode='group'
    )
    
    return fig_comparison, comparison_df

def create_performance_traffic_light(df, expected_dist):
    """Gráfico tipo semáforo para evaluar cumplimiento por unidad"""
    
    # Análisis por unidad organizativa
    unit_analysis = []
    
    for unit in df['UNIDAD_ORGANIZATIVA'].unique():
        unit_data = df[df['UNIDAD_ORGANIZATIVA'] == unit]
        unit_dist = unit_data['BANDA_DESEMPEÑO'].value_counts(normalize=True) * 100
        
        # Calcular score de cumplimiento
        score = 0
        for banda_display, banda_key in [
            ('Muy por debajo (100-179)', 'muy_por_debajo'),
            ('Por debajo (180-259)', 'por_debajo'),
            ('Dentro esperado (260-339)', 'dentro_esperado'),
            ('Sobre esperado (340-419)', 'sobre_esperado'),
            ('Excepcional (420-500)', 'excepcional')
        ]:
            real_pct = unit_dist.get(banda_display, 0)
            expected_pct = expected_dist[banda_key]
            deviation = abs(real_pct - expected_pct)
            score += max(0, 20 - deviation)
        
        # Determinar color del semáforo
        if score >= 80:
            color = 'green'
            status = '🟢 Excelente'
        elif score >= 60:
            color = 'yellow'
            status = '🟡 Aceptable'
        else:
            color = 'red'
            status = '🔴 Requiere atención'
        
        # SOLUCIÓN: Asegurar que Total_Empleados no sea NaN
        total_empleados = len(unit_data)
        if total_empleados == 0 or pd.isna(total_empleados):
            total_empleados = 1  # Valor mínimo para evitar NaN
        
        unit_analysis.append({
            'Unidad': unit[:30] + '...' if len(unit) > 30 else unit,
            'Score': score,
            'Status': status,
            'Color': color,
            'Total_Empleados': total_empleados
        })
    
    unit_df = pd.DataFrame(unit_analysis)
    
    # SOLUCIÓN ADICIONAL: Limpiar cualquier NaN restante
    unit_df['Total_Empleados'] = unit_df['Total_Empleados'].fillna(1)
    unit_df['Score'] = unit_df['Score'].fillna(0)
    
    # Gráfico de burbujas semáforo
    fig_traffic = px.scatter(
        unit_df,
        x='Unidad',
        y='Score',
        size='Total_Empleados',  # Ahora sin NaN
        color='Color',
        color_discrete_map={'green': '#00FF00', 'yellow': '#FFFF00', 'red': '#FF0000'},
        title='Semáforo de Cumplimiento por Unidad Organizativa',
        hover_data=['Status', 'Total_Empleados']
    )
    
    fig_traffic.update_layout(
        xaxis_tickangle=45,
        height=600,
        yaxis_title='Score de Cumplimiento (0-100)'
    )
    
    return fig_traffic, unit_df

def clean_dataframe_for_analysis(df):
    """Limpia el DataFrame para evitar errores en los gráficos"""
    
    # Limpiar valores NaN en columnas críticas
    df['RESULTADO_CUANTITATIVO'] = df['RESULTADO_CUANTITATIVO'].fillna(0)
    df['DIAS_A_PAGAR'] = df['DIAS_A_PAGAR'].fillna(0)
    
    # Asegurar que las columnas de texto no tengan NaN
    df['UNIDAD_ORGANIZATIVA'] = df['UNIDAD_ORGANIZATIVA'].fillna('Sin Unidad')
    df['CARGO'] = df['CARGO'].fillna('Sin Cargo')
    df['AREA_PERSONAL'] = df['AREA_PERSONAL'].fillna('Sin Área')
    
    # Eliminar filas completamente vacías
    df = df.dropna(how='all')
    
    return df


def create_responsive_dataframe(df, max_rows_mobile=10):
    """Crea tablas responsivas según el dispositivo"""
    
    if st.session_state.get('mobile_detected', False):
        # En móvil, mostrar menos filas y columnas esenciales
        essential_cols = ['NOMBRE', 'RESULTADO_CUANTITATIVO', 'EVALUACION', 'DIAS_A_PAGAR']
        mobile_df = df[essential_cols].head(max_rows_mobile)
        
        st.dataframe(
            mobile_df,
            use_container_width=True,
            height=300
        )
        
        if len(df) > max_rows_mobile:
            st.info(f"Mostrando {max_rows_mobile} de {len(df)} registros. Use filtros para ver más.")
            
    else:
        # Vista completa para desktop
        st.dataframe(df, use_container_width=True)


def get_chart_height(is_mobile=False):
    """Devuelve altura de gráfico según el dispositivo"""
    return 400 if is_mobile else 600

def create_adaptive_plotly_chart(fig, title=""):
    """Crea gráficos adaptativos"""
    is_mobile = st.session_state.get('mobile_detected', False)
    height = get_chart_height(is_mobile)
    
    fig.update_layout(
        height=height,
        title_font_size=14 if is_mobile else 16,
        margin=dict(l=20, r=20, t=40, b=20) if is_mobile else dict(l=50, r=50, t=60, b=50)
    )
    
    st.plotly_chart(fig, use_container_width=True)


def create_adaptive_menu():
    """Crea un menú que se adapta al dispositivo"""
    
    if st.session_state.get('mobile_detected', False):
        # Menú simplificado para móvil
        menu_option = [
            "🏠 Dashboard Principal",
            "📊 Análisis Descriptivo",
            "🎯 Gráficos 3D",
            "📈 Distribuciones",
            "🎯 Análisis por Bandas y Cuotas",
            "📤 Exportaciones"
        ]
    else:
        # Menú completo para desktop
        menu_option = [
            "🏠 Dashboard Principal",
            "📊 Análisis Descriptivo",
            "🎯 Gráficos 3D",
            "📈 Distribuciones",
            "🔄 Comparativos",
            "🎯 Análisis por Bandas y Cuotas",
            "📋 Datos Detallados",
            "📤 Exportaciones"
        ]
    return st.sidebar.selectbox("Seleccione el análisis:", menu_option)




# Aplicación principal
def main():
    # Inyectar CSS responsivo
    inject_mobile_css()
    
    # Configurar detección de dispositivo
    setup_device_detection()

    st.title("📊 Análisis de Evaluación de Desempeño BANCOEX")

   # Título adaptativo
    if st.session_state.get('mobile_detected', False):
        st.markdown("### Resultados 3er Trimestre 2025")
    else:
        st.markdown("### Análisis Integral de Resultados del 3er Trimestre 2025")
    
    # Cargar datos - priorizar archivo subido si existe
    uploaded_df = load_file_uploader()
    
    if uploaded_df is not None:
        df = uploaded_df
        st.info("🔄 Usando archivo subido por el usuario")
    else:
        df = load_and_process_data()
    
    # Validar que tenemos datos
    if df is None or len(df) == 0:
        st.error("No se pudieron cargar los datos. Verifique el archivo.")
        st.stop()
    
    # Mostrar información del dataset cargado
    with st.expander("📋 Información del Dataset"):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write(f"**Total de registros:** {len(df)}")
        with col2:
            st.write(f"**Columnas disponibles:** {len(df.columns)}")
        with col3:
            st.write(f"**Rango de puntuaciones:** {df['RESULTADO_CUANTITATIVO'].min():.0f} - {df['RESULTADO_CUANTITATIVO'].max():.0f}")
        
        # Mostrar las primeras filas
        st.dataframe(df.head(), use_container_width=True)
    
    # Sidebar para navegación
    st.sidebar.title("🎛️ Panel de Control")
    
    # Mostrar estadísticas rápidas en el sidebar
    st.sidebar.markdown("### 📈 Estadísticas Rápidas")
    st.sidebar.metric("Total Evaluados", len(df))
    st.sidebar.metric("Puntuación Promedio", f"{df['RESULTADO_CUANTITATIVO'].mean():.1f}")
    excepcional_count = len(df[df['EVALUACION'].str.contains('Excepcional', na=False)])
    st.sidebar.metric("Desempeño Excepcional", excepcional_count)
    
    menu_option = create_adaptive_menu()

    if menu_option == "🏠 Dashboard Principal":
        st.subheader("Vista General del Sistema")
        
        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Evaluados", len(df), delta="293 empleados")
        with col2:
            avg_score = df['RESULTADO_CUANTITATIVO'].mean()
            st.metric("Puntuación Promedio", f"{avg_score:.1f}", 
                     delta=f"{avg_score - 350:.1f} vs esperado")
        with col3:
            excepcional = len(df[df['EVALUACION'] == 'Sobresaliente / Excepcional'])
            st.metric("Desempeño Excepcional", f"{excepcional}", 
                     delta=f"{(excepcional/len(df)*100):.1f}%")
        with col4:
            avg_days = df['DIAS_A_PAGAR'].mean()
            st.metric("Días Promedio Bono", f"{avg_days:.0f}", delta="días")
        
        # Gráfico principal
        fig_main = px.sunburst(
            df,
            path=['AREA_PERSONAL', 'EVALUACION'],
            values='DIAS_A_PAGAR',
            title="Distribución Jerárquica: Área → Evaluación → Días de Bono"
        )
        st.plotly_chart(fig_main, use_container_width=True)
        
    elif menu_option == "📊 Análisis Descriptivo":
        analysis_results = descriptive_analysis(df)
        
        # Tabla de correlaciones
        st.subheader("Matriz de Correlaciones")
        corr_matrix = df[['RESULTADO_CUANTITATIVO', 'DIAS_A_PAGAR', 'ANTIGUEDAD_AÑOS']].corr()
        fig_corr = px.imshow(
            corr_matrix,
            text_auto=True,
            aspect="auto",
            title="Correlaciones entre Variables Numéricas"
        )
        st.plotly_chart(fig_corr, use_container_width=True)
        
    elif menu_option == "🎯 Gráficos 3D":
        st.subheader("Visualizaciones 3D Avanzadas")
        
        tab1, tab2 = st.tabs(["🎯 Distribución por Área", "🌊 Superficie de Rendimiento"])
        
        with tab1:
            fig_3d_area = create_3d_area_performance(df)
            st.plotly_chart(fig_3d_area, use_container_width=True)
            
        with tab2:
            fig_3d_surface = create_3d_performance_surface(df)
            st.plotly_chart(fig_3d_surface, use_container_width=True)
    
    elif menu_option == "📈 Distribuciones":
        st.subheader("Análisis de Distribuciones")
        
        # Histogramas múltiples
        fig_hist = create_distribution_histogram(df)
        st.plotly_chart(fig_hist, use_container_width=True)
        
        # Boxplots por área
        fig_box = px.box(
            df,
            x='AREA_PERSONAL',
            y='RESULTADO_CUANTITATIVO',
            color='EVALUACION',
            title="Distribución de Puntuaciones por Área y Evaluación"
        )
        fig_box.update_xaxes(tickangle=45)
        st.plotly_chart(fig_box, use_container_width=True)
        
    elif menu_option == "🔄 Comparativos":
        st.subheader("Análisis Comparativo")
        
        # Comparativo por área
        area_comparison = df.groupby('AREA_PERSONAL').agg({
            'RESULTADO_CUANTITATIVO': ['mean', 'std'],
            'DIAS_A_PAGAR': 'mean'
        }).round(2)
        
        area_comparison.columns = ['Puntuación_Media', 'Desviación_Std', 'Días_Promedio']
        area_comparison = area_comparison.reset_index()
        
        fig_comparison = px.scatter(
            area_comparison,
            x='Puntuación_Media',
            y='Días_Promedio',
            size='Desviación_Std',
            color='AREA_PERSONAL',
            title="Comparativo: Puntuación vs Días de Bono por Área"
        )
        st.plotly_chart(fig_comparison, use_container_width=True)
        
        # Radar chart
        st.subheader("Perfil de Rendimiento por Área")
        
        # Preparar datos para radar
        radar_data = df.groupby('AREA_PERSONAL').agg({
            'RESULTADO_CUANTITATIVO': 'mean'
        }).reset_index()
        
        # Normalizar puntuaciones a escala 0-100
        radar_data['Score_Normalized'] = (radar_data['RESULTADO_CUANTITATIVO'] - 100) / 400 * 100
        
        fig_radar = go.Figure()
        
        for area in radar_data['AREA_PERSONAL']:
            score = radar_data[radar_data['AREA_PERSONAL'] == area]['Score_Normalized'].iloc[0]
            
            fig_radar.add_trace(go.Scatterpolar(
                r=[score, score, score, score],
                theta=['Rendimiento', 'Consistencia', 'Potencial', 'Evaluación'],
                fill='toself',
                name=area
            ))
        
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            title="Perfil de Rendimiento Multidimensional",
            showlegend=True
        )
        
        st.plotly_chart(fig_radar, use_container_width=True)
    elif menu_option == "🎯 Análisis por Bandas y Cuotas":  # <-- AGREGAR DESDE AQUÍ
        st.subheader("Análisis de Bandas de Desempeño y Cumplimiento de Cuotas")
    
        # Crear bandas
        df = create_performance_bands(df)
    
        # Solicitar cuotas esperadas
        expected_dist = get_expected_distribution()
    
        if expected_dist:
            tab1, tab2, tab3, tab4 = st.tabs([
                "📊 Dispersión 3D por Unidades", 
                "⚖️ Real vs Esperado", 
                "🚦 Semáforo de Cumplimiento",
                "📋 Análisis por Cargos"
            ])
        
            with tab1:
                fig_3d_scatter = create_3d_scatter_by_unit(df)
                st.plotly_chart(fig_3d_scatter, use_container_width=True)
        
            with tab2:
                fig_comparison, comparison_df = create_real_vs_expected_analysis(df, expected_dist)
                st.plotly_chart(fig_comparison, use_container_width=True)
                st.dataframe(comparison_df, use_container_width=True)
        
            with tab3:
                fig_traffic, traffic_df = create_performance_traffic_light(df, expected_dist)
                st.plotly_chart(fig_traffic, use_container_width=True)
                st.dataframe(traffic_df, use_container_width=True)
        
            with tab4:
                cargo_band_analysis = df.groupby(['CARGO', 'BANDA_DESEMPEÑO']).size().unstack(fill_value=0)
            
                fig_cargo_heatmap = px.imshow(
                    cargo_band_analysis,
                    title="Mapa de Calor: Distribución de Cargos por Banda de Desempeño",
                    aspect="auto",
                    color_continuous_scale="RdYlGn"
                )
                st.plotly_chart(fig_cargo_heatmap, use_container_width=True)  # <-- HASTA AQUÍ   

    elif menu_option == "📋 Datos Detallados":
        st.subheader("Vista Detallada de los Datos")
        
        # Filtros para explorar los datos
        col1, col2, col3 = st.columns(3)
        
        with col1:
            areas_disponibles = ['Todas'] + sorted(df['AREA_PERSONAL'].unique().tolist())
            area_filtro = st.selectbox("Filtrar por Área", areas_disponibles)
        
        with col2:
            evaluaciones_disponibles = ['Todas'] + sorted(df['EVALUACION'].unique().tolist())
            eval_filtro = st.selectbox("Filtrar por Evaluación", evaluaciones_disponibles)
        
        with col3:
            rango_puntuacion = st.slider(
                "Rango de Puntuación",
                int(df['RESULTADO_CUANTITATIVO'].min()),
                int(df['RESULTADO_CUANTITATIVO'].max()),
                (int(df['RESULTADO_CUANTITATIVO'].min()), int(df['RESULTADO_CUANTITATIVO'].max()))
            )
        
        # Aplicar filtros
        df_filtrado = df.copy()
        
        if area_filtro != 'Todas':
            df_filtrado = df_filtrado[df_filtrado['AREA_PERSONAL'] == area_filtro]
        
        if eval_filtro != 'Todas':
            df_filtrado = df_filtrado[df_filtrado['EVALUACION'] == eval_filtro]
        
        df_filtrado = df_filtrado[
            (df_filtrado['RESULTADO_CUANTITATIVO'] >= rango_puntuacion[0]) &
            (df_filtrado['RESULTADO_CUANTITATIVO'] <= rango_puntuacion[1])
        ]
        
        st.write(f"**Mostrando {len(df_filtrado)} de {len(df)} registros**")
        
        # Mostrar datos filtrados
        st.dataframe(
            df_filtrado[['NOMBRE', 'AREA_PERSONAL', 'CARGO', 'RESULTADO_CUANTITATIVO', 'EVALUACION', 'DIAS_A_PAGAR']],
            use_container_width=True
        )
        
        # Resumen de los datos filtrados
        if len(df_filtrado) > 0:
            st.subheader("Resumen de Datos Filtrados")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Registros", len(df_filtrado))
            with col2:
                st.metric("Puntuación Media", f"{df_filtrado['RESULTADO_CUANTITATIVO'].mean():.1f}")
            with col3:
                st.metric("Días Promedio", f"{df_filtrado['DIAS_A_PAGAR'].mean():.1f}")
            with col4:
                st.metric("Antigüedad Media", f"{df_filtrado['ANTIGUEDAD_AÑOS'].mean():.1f} años")
        
    elif menu_option == "📤 Exportaciones":
        st.subheader("Opciones de Exportación")
        
        analysis_results = descriptive_analysis(df)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📊 Exportar a Excel")
            st.write("Incluye todos los datos, estadísticas descriptivas y análisis por área.")
            
            if st.button("🔽 Descargar Excel", type="primary"):
                excel_file = export_to_excel(df, analysis_results)
                st.download_button(
                    label="📥 Descargar Archivo Excel",
                    data=excel_file,
                    file_name=f"analisis_desempeño_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        
        with col2:
            st.markdown("### 📄 Exportar Reporte PDF")
            st.write("Reporte ejecutivo con gráficos y análisis principales.")
            
            if st.button("🔽 Generar PDF", type="secondary"):
                pdf_file = generate_pdf_report(df, analysis_results)
                st.download_button(
                    label="📥 Descargar Reporte PDF",
                    data=pdf_file,
                    file_name=f"reporte_desempeño_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf"
                )
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666; font-size: 12px;'>
            Desarrollado por MSC. Jesús F. Salazar Rojas / Bajo Python ® / Septiembre 2025
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()