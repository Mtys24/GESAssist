import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

# Cargar variables de entorno
load_dotenv()

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

El objetivo es apoyar el análisis de casos médicos mediante visualizaciones simples e interactivas y asistencia de IA.
""")

tab1, tab2 = st.tabs(["📊 Dashboard Interactivo", "🤖 Asistente IA"])

with tab1:
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
    else:
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
        def convert_df(df_to_download):
            return df_to_download.to_csv(index=False).encode('utf-8')
        
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

with tab2:
    st.header("🤖 Asistente IA (Llama-3)")
    st.markdown("Consulta a nuestro modelo avanzado si un perfil etario y diagnóstico tiene alta probabilidad de ser clasificado como GES.")
    
    hf_token = os.getenv("HF_TOKEN")
    
    if not hf_token or hf_token == "hf_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX":
        st.warning("⚠️ **Asistente IA desactivado:** No se ha detectado un token válido de HuggingFace (`HF_TOKEN`) en el archivo `.env`. Configura el archivo `.env` en el directorio raíz para activar esta función.")
    else:
        st.success("✅ Conectado a Hugging Face.")
        
        with st.form("ia_form"):
            user_diagnostic = st.text_input("Ingresa un diagnóstico (ej. Catarata, Cáncer de Mama, Apendicitis):")
            user_age = st.number_input("Ingresa la edad del paciente:", min_value=0, max_value=120, value=30)
            
            submit_button = st.form_submit_button("Consultar Modelo")
            
            if submit_button:
                if user_diagnostic.strip() == "":
                    st.error("Por favor, ingresa un diagnóstico válido.")
                else:
                    with st.spinner("Analizando datos históricos y consultando a Llama-3..."):
                        try:
                            # 1. RAG: Búsqueda de probabilidad empírica en el dataset
                            diag_upper = user_diagnostic.upper().strip()
                            df_rag = df[df["diagnostic"].str.contains(diag_upper, case=False, na=False)]
                            df_rag = df_rag[(df_rag["age"] >= user_age - 5) & (df_rag["age"] <= user_age + 5)]
                            
                            total_similares = len(df_rag)
                            ges_similares = df_rag["ges"].sum() if total_similares > 0 else 0
                            
                            if total_similares > 0:
                                prob_empirica = (ges_similares / total_similares) * 100
                                rag_context = f"DATO EMPÍRICO ESTADÍSTICO: En nuestro dataset histórico local, encontramos {total_similares} casos similares (pacientes entre {max(0, user_age-5)} y {user_age+5} años con diagnóstico asociado a '{user_diagnostic}'). De ellos, el {prob_empirica:.1f}% fue clasificado como GES. Debes mencionar obligatoriamente este porcentaje en tu respuesta y justificar por qué tiene o no sentido clínico."
                            else:
                                prob_empirica = 0
                                rag_context = f"DATO EMPÍRICO ESTADÍSTICO: No encontramos ningún caso histórico en el dataset para el diagnóstico asociado a '{user_diagnostic}' en un rango de edad de +/- 5 años. Menciona esto e indica que podría ser una condición atípica para esa edad."

                            # 2. Renderizado del Gráfico de Precisión (Gauge Chart)
                            st.markdown("### 📊 Precisión / Probabilidad Histórica")
                            fig_gauge = go.Figure(go.Indicator(
                                mode="gauge+number",
                                value=prob_empirica,
                                title={'text': f"Probabilidad GES (%)<br><span style='font-size:0.8em;color:gray'>Basado en {total_similares} casos históricos similares</span>"},
                                gauge={
                                    'axis': {'range': [0, 100]},
                                    'bar': {'color': "#1a2b4c"},
                                    'steps': [
                                        {'range': [0, 33], 'color': "#ff9999"},
                                        {'range': [33, 66], 'color': "#ffe680"},
                                        {'range': [66, 100], 'color': "#b3ffb3"}
                                    ],
                                }
                            ))
                            st.plotly_chart(fig_gauge, use_container_width=True)
                            
                            # 3. Llamada al Modelo Llama-3
                            client = InferenceClient(model="meta-llama/Meta-Llama-3-8B-Instruct", token=hf_token)
                            
                            system_prompt = """Eres un experto médico y auditor del sistema de salud en Chile.
MUY IMPORTANTE: "GES" significa "Garantías Explícitas en Salud" (Decreto Supremo N° 29).

Al evaluar si un caso tiene probabilidad de ser GES, DEBES considerar y mencionar las siguientes Reglas Duras de Elegibilidad:
1. Previsión: El paciente debe pertenecer a FONASA o ISAPRE (Excluye FF.AA. y Particulares).
2. Red Cerrada: El paciente debe atenderse en la red definida por su seguro, no por libre elección.
3. Formalidad: Se requiere el Formulario de Constancia GES firmado por el médico.
4. Canasta: Solo se cubre lo definido en el arancel; tratamientos más caros o experimentales quedan 'fuera de canasta'.
5. Edad: La edad es determinista. Ej. Artrosis de Cadera primaria es solo para mayores de 65 años. Escoliosis es para menores de 25 años. Catarata general es >15 años.
6. Ley Salud Mental: En salud mental, las Isapres no pueden rechazar cobertura argumentando enfermedades preexistentes (Ley 21.331).
7. Pérdida de derecho: Se pierde la garantía por 2 inasistencias médicas consecutivas.

Evalúa el diagnóstico y la edad proporcionada por el usuario. Cruza esta información con el dato estadístico (probabilidad) que se te inyectará en el prompt del usuario. Si la probabilidad es baja, evalúa si es porque choca con alguna regla de edad. Si la probabilidad es alta, recuérdale al usuario las obligaciones administrativas (Formulario, Red Cerrada).

Responde SIEMPRE en español, de forma estructurada, profesional y citando explícitamente estas normativas de elegibilidad."""

                            user_prompt = f"Paciente de {user_age} años con diagnóstico de '{user_diagnostic}'. Analiza este caso bajo el contexto GES. \n\n{rag_context}"

                            
                            messages = [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_prompt}
                            ]
                            
                            response = client.chat_completion(messages=messages, max_tokens=1000)
                            
                            st.write("### Respuesta de la IA:")
                            st.write(response.choices[0].message.content)
                            
                        except Exception as e:
                            st.error(f"Error al conectar con la API de Hugging Face: {e}")