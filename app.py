import streamlit as st
import pandas as pd
import plotly.express as px

# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

st.set_page_config(
    page_title="GESAssist - Clasificación GES",
    page_icon="🏥",
    layout="wide"
)

st.markdown("""
<style>
    /* Estilos Premium / WOW Factor */
    .stApp {
        background-color: #f4f6f9;
    }
    h1, h2, h3 {
        color: #1a2b4c !important;
        font-family: 'Inter', sans-serif;
    }
    /* Estilo de tarjetas para métricas */
    [data-testid="metric-container"] {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        border-left: 5px solid #3498db;
        transition: transform 0.2s ease;
    }
    [data-testid="metric-container"]:hover {
        transform: translateY(-3px);
    }
    [data-testid="stMetricValue"] {
        color: #2c3e50 !important;
        font-size: 2rem !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# CARGA DE DATOS
# ============================================================

@st.cache_data
def cargar_datos():
    df = pd.read_csv("data/dataset_limpio.csv")
    return df

df = cargar_datos()

# ============================================================
# TÍTULO Y DESCRIPCIÓN
# ============================================================

st.title("🏥 GESAssist: Análisis de Diagnósticos GES")

st.markdown("""
Este dashboard permite explorar un dataset de diagnósticos médicos clasificados según si corresponden o no a una condición GES.

El objetivo es apoyar el análisis de casos médicos mediante visualizaciones simples e interactivas.
""")

# ============================================================
# FILTROS INTERACTIVOS
# ============================================================

st.sidebar.header("Filtros interactivos")

edad_min = int(df["age"].min())
edad_max = int(df["age"].max())

rango_edad = st.sidebar.slider(
    "Rango de edad",
    min_value=edad_min,
    max_value=edad_max,
    value=(edad_min, edad_max)
)

opcion_ges = st.sidebar.selectbox(
    "Tipo de caso",
    options=["Todos", "GES", "No GES"]
)

buscar_diagnostico = st.sidebar.text_input(
    "Buscar diagnóstico",
    placeholder="Ej: CATARATA, CANCER, HERNIA..."
)

# ============================================================
# APLICAR FILTROS
# ============================================================

df_filtrado = df[
    (df["age"] >= rango_edad[0]) &
    (df["age"] <= rango_edad[1])
].copy()

if opcion_ges == "GES":
    df_filtrado = df_filtrado[df_filtrado["ges"] == True]
elif opcion_ges == "No GES":
    df_filtrado = df_filtrado[df_filtrado["ges"] == False]

if buscar_diagnostico.strip() != "":
    texto = buscar_diagnostico.upper().strip()
    df_filtrado = df_filtrado[
        df_filtrado["diagnostic"].str.contains(texto, case=False, na=False)
    ]

# ============================================================
# MÉTRICAS PRINCIPALES
# ============================================================

total_casos = len(df_filtrado)
casos_ges = int(df_filtrado["ges"].sum()) if total_casos > 0 else 0
casos_no_ges = total_casos - casos_ges
porcentaje_ges = (casos_ges / total_casos * 100) if total_casos > 0 else 0

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total de casos", total_casos)
col2.metric("Casos GES", casos_ges)
col3.metric("Casos No GES", casos_no_ges)
col4.metric("% GES", f"{porcentaje_ges:.1f}%")

st.divider()

if total_casos == 0:
    st.warning("No hay datos para los filtros seleccionados.")
    st.stop()

# ============================================================
# VISUALIZACIÓN 1
# ============================================================

st.subheader("1. Distribución de casos GES y No GES")

conteo_ges = df_filtrado["ges"].map({
    True: "GES",
    False: "No GES"
}).value_counts().reset_index()

conteo_ges.columns = ["Clasificación", "Cantidad"]

fig1 = px.bar(
    conteo_ges,
    x="Clasificación",
    y="Cantidad",
    text="Cantidad",
    title="Cantidad de casos según clasificación GES"
)

fig1.update_traces(textposition="outside")
st.plotly_chart(fig1, use_container_width=True)

# ============================================================
# VISUALIZACIÓN 2
# ============================================================

st.subheader("2. Distribución de edad de los pacientes")

df_filtrado["clasificacion"] = df_filtrado["ges"].map({
    True: "GES",
    False: "No GES"
})

fig2 = px.histogram(
    df_filtrado,
    x="age",
    color="clasificacion",
    nbins=20,
    title="Distribución de edades según clasificación GES",
    labels={"age": "Edad", "clasificacion": "Clasificación"}
)

st.plotly_chart(fig2, use_container_width=True)

# ============================================================
# VISUALIZACIÓN 3
# ============================================================

st.subheader("3. Diagnósticos más frecuentes")

top_n = st.slider(
    "Cantidad de diagnósticos a mostrar",
    min_value=5,
    max_value=20,
    value=10
)

top_diagnosticos = (
    df_filtrado["diagnostic"]
    .value_counts()
    .head(top_n)
    .reset_index()
)

top_diagnosticos.columns = ["Diagnóstico", "Cantidad"]

fig3 = px.bar(
    top_diagnosticos,
    x="Cantidad",
    y="Diagnóstico",
    orientation="h",
    text="Cantidad",
    title=f"Top {top_n} diagnósticos más frecuentes"
)

fig3.update_layout(yaxis={"categoryorder": "total ascending"})
st.plotly_chart(fig3, use_container_width=True)

# ============================================================
# VISUALIZACIÓN 4
# ============================================================

st.subheader("4. Casos por grupo etario")

df_filtrado["grupo_edad"] = pd.cut(
    df_filtrado["age"],
    bins=[0, 18, 30, 45, 60, 75, 100],
    labels=["0-18", "19-30", "31-45", "46-60", "61-75", "76+"]
)

grupo_edad = (
    df_filtrado
    .groupby(["grupo_edad", "clasificacion"], observed=False)
    .size()
    .reset_index(name="Cantidad")
)

fig4 = px.bar(
    grupo_edad,
    x="grupo_edad",
    y="Cantidad",
    color="clasificacion",
    barmode="group",
    title="Cantidad de casos por grupo etario",
    labels={
        "grupo_edad": "Grupo de edad",
        "clasificacion": "Clasificación"
    }
)

st.plotly_chart(fig4, use_container_width=True)

# ============================================================
# TABLA
# ============================================================

st.subheader("Datos filtrados")

st.dataframe(
    df_filtrado[["id", "diagnostic", "age", "ges"]],
    use_container_width=True
)

st.markdown("<br>", unsafe_allow_html=True)

# Opción de descarga
@st.cache_data
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8')

csv_data = convert_df(df_filtrado)

st.download_button(
    label="📥 Descargar datos filtrados (CSV)",
    data=csv_data,
    file_name='dataset_filtrado_ges.csv',
    mime='text/csv',
)

# ============================================================
# HALLAZGO PRINCIPAL
# ============================================================

st.divider()

st.subheader("Hallazgo principal")

st.markdown(f"""
En el conjunto filtrado se observan **{total_casos} casos**, de los cuales 
**{casos_ges} corresponden a GES** y **{casos_no_ges} no corresponden a GES**.

El análisis muestra que la clasificación GES no depende únicamente del nombre del diagnóstico. 
También puede estar relacionada con la edad del paciente y con la forma específica en que aparece registrado el diagnóstico.
""")

st.info(
    "Este dashboard no reemplaza una evaluación médica. Su objetivo es apoyar el análisis exploratorio de los datos."
)