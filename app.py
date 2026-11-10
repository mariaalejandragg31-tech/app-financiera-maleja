import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import yfinance as yf

st.set_page_config(
    page_title="MALEJA | Analítica Financiera",
    page_icon="📊",
    layout="wide"
)


st.markdown("""
<style>
.stApp {
    background-color: #101827;
    color: #FFFFFF;
}

[data-testid="stSidebar"] {
    background-color: #172438;
}

[data-testid="stSidebar"] * {
    color: #FFFFFF !important;
}

[data-testid="stMetric"] {
    background-color: #1D2D43;
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #D6A84B;
}

[data-testid="stMetricLabel"] {
    color: #FFFFFF !important;
}

[data-testid="stMetricValue"] {
    color: #F2C45B !important;
}

h1, h2, h3 {
    color: #E7B84B;
}

.stDownloadButton button {
    background-color: #D6A84B !important;
    color: #101827 !important;
    border: none !important;
    font-weight: bold !important;
    border-radius: 8px !important;
}

.stDownloadButton button:hover {
    background-color: #F2C45B !important;
    color: #101827 !important;
}

.stButton button {
    background-color: #D6A84B;
    color: #101827;
}

</style>
""", unsafe_allow_html=True)


ACTIVOS = {
    "Oro": "GC=F",
    "Petróleo WTI": "CL=F",
    "Café": "KC=F"
}

@st.cache_data(ttl=3600)
def descargar_datos(inicio, fin):
    resultados = {}

    fin_exclusivo = (
        pd.Timestamp(fin) + pd.Timedelta(days=1)
    )

    for nombre, ticker in ACTIVOS.items():

        try:
            df = yf.download(
                ticker,
                start=str(inicio),
                end=fin_exclusivo.strftime("%Y-%m-%d"),
                auto_adjust=True,
                progress=False
            )

            if df.empty:
                continue

            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            df = df.reset_index()

            if "Date" not in df.columns:
                df = df.rename(columns={"Datetime": "Date"})

            df = df.dropna(subset=["Close"])

            resultados[nombre] = df

        except Exception as e:
            st.warning(f"No se pudo descargar {nombre}: {e}")

    return resultados


def calcular_indicadores(datos):

    resultados = {}

    for nombre, df in datos.items():

        precios = df["Close"].dropna()

        rendimientos = precios.pct_change().dropna()

        if len(precios) < 2:
            continue

        resultados[nombre] = {
            "Precio inicial": precios.iloc[0],
            "Precio final": precios.iloc[-1],
            "Rendimiento acumulado": (
                precios.iloc[-1] / precios.iloc[0] - 1
            ),
            "Volatilidad anualizada": (
                rendimientos.std() * np.sqrt(252)
            ),
            "Precio máximo": precios.max(),
            "Precio mínimo": precios.min()
        }

    return pd.DataFrame(resultados).T


# ENCABEZADO
st.title("📊 APP FINANCIERA MALEJA")

st.markdown(
    "### Análisis histórico de commodities internacionales"
)

st.caption(
    "Ingeniería Financiera | ITM | IX Concurso 2026"
)

st.divider()

# MENÚ
st.sidebar.title("MALEJA")
st.sidebar.caption("Panel de análisis financiero")

pagina = st.sidebar.radio(
    "NAVEGACIÓN",
    [
        "Inicio",
        "Análisis individual",
        "Comparación",
        "Riesgo y volatilidad",
        "Datos y metodología"
    ]
)

st.sidebar.divider()

st.sidebar.subheader("Filtros")

fecha_inicio = st.sidebar.date_input(
    "Fecha inicial",
    value=pd.Timestamp("2021-11-05").date(),
    min_value=pd.Timestamp("2021-11-05").date(),
    max_value=pd.Timestamp("2026-11-05").date()
)

fecha_fin = st.sidebar.date_input(
    "Fecha final",
    value=pd.Timestamp("2026-11-05").date(),
    min_value=pd.Timestamp("2021-11-05").date(),
    max_value=pd.Timestamp("2026-11-05").date()
)

if fecha_inicio >= fecha_fin:
    st.error("La fecha inicial debe ser anterior a la fecha final.")
    st.stop()

with st.spinner("Consultando los mercados financieros..."):
    datos = descargar_datos(fecha_inicio, fecha_fin)

if not datos:
    st.error("No se encontraron datos. Intenta nuevamente.")
    st.stop()

indicadores = calcular_indicadores(datos)

if indicadores.empty:
    st.error("No hay suficientes datos para calcular indicadores.")
    st.stop()

# NORMALIZACIÓN
normalizados = {}

for nombre, df in datos.items():

    serie = df.set_index("Date")["Close"].dropna()

    normalizados[nombre] = (
        serie / serie.iloc[0]
    ) * 100

precios_base100 = pd.DataFrame(normalizados)

# INICIO
if pagina == "Inicio":

    st.header("Resumen del mercado")

    st.write(
        "Bienvenido a MALEJA, una herramienta de analítica "
        "financiera para estudiar el comportamiento histórico "
        "del oro, petróleo WTI y café."
    )

    st.info(
        "Esta aplicación analiza datos históricos. "
        "No constituye asesoría financiera ni predice precios futuros."
    )

    columnas = st.columns(len(indicadores))

    for columna, (nombre, fila) in zip(
        columnas, indicadores.iterrows()
    ):

        columna.metric(
            nombre,
            f"{fila['Rendimiento acumulado']:.2%}",
            help="Rendimiento acumulado del período seleccionado"
        )

    st.subheader("Evolución comparativa")

    fig = px.line(
        precios_base100,
        title="Evolución de los commodities - Base 100"
    )

    fig.update_layout(
        template="plotly_dark",
        height=500
    )

    st.plotly_chart(fig, use_container_width=True)

    st.caption(
        f"Período: {fecha_inicio} hasta {fecha_fin}"
    )

# ANÁLISIS INDIVIDUAL
elif pagina == "Análisis individual":

    st.header("Análisis individual")

    activo = st.selectbox(
        "Selecciona un commodity",
        list(datos.keys())
    )

    df = datos[activo]

    fig = px.line(
        df,
        x="Date",
        y="Close",
        title=f"Histórico de precios: {activo}"
    )

    fig.update_layout(template="plotly_dark", height=450)

    st.plotly_chart(fig, use_container_width=True)

    fila = indicadores.loc[activo]

    c1, c2, c3 = st.columns(3)

    c1.metric("Precio inicial", f"{fila['Precio inicial']:,.2f}")
    c2.metric("Precio final", f"{fila['Precio final']:,.2f}")
    c3.metric(
        "Rendimiento acumulado",
        f"{fila['Rendimiento acumulado']:.2%}"
    )

    st.subheader("Datos históricos")

    st.dataframe(df, use_container_width=True)

# COMPARACIÓN
elif pagina == "Comparación":

    st.header("Comparación de commodities")

    seleccionados = st.multiselect(
        "Activos que deseas comparar",
        list(datos.keys()),
        default=list(datos.keys())
    )

    if seleccionados:

        fig = px.line(
            precios_base100[seleccionados],
            title="Comparación de evolución - Base 100"
        )

        fig.update_layout(template="plotly_dark")

        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Indicadores comparativos")

        st.dataframe(
            indicadores.loc[seleccionados].style.format({
                "Rendimiento acumulado": "{:.2%}",
                "Volatilidad anualizada": "{:.2%}"
            }),
            use_container_width=True
        )

    else:
        st.warning("Selecciona al menos un activo.")

# RIESGO
elif pagina == "Riesgo y volatilidad":

    st.header("Análisis de riesgo y volatilidad")

    st.write(
        "La volatilidad mide la dispersión de los rendimientos "
        "diarios y permite describir la variabilidad histórica."
    )

    volatilidad = indicadores[
        ["Volatilidad anualizada"]
    ].reset_index()

    volatilidad.columns = [
        "Activo",
        "Volatilidad"
    ]

    volatilidad["Porcentaje"] = (
        volatilidad["Volatilidad"] * 100
    )

    fig = px.bar(
        volatilidad,
        x="Activo",
        y="Porcentaje",
        color="Activo",
        title="Volatilidad anualizada"
    )

    fig.update_layout(template="plotly_dark")

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Resultados")

    st.dataframe(
        indicadores.style.format({
            "Rendimiento acumulado": "{:.2%}",
            "Volatilidad anualizada": "{:.2%}"
        }),
        use_container_width=True
    )

# DATOS Y METODOLOGÍA
elif pagina == "Datos y metodología":

    st.header("Datos y metodología")

    st.markdown("""
    ### Fuente de información

    Yahoo Finance, consultado mediante yfinance.

    ### Activos estudiados

    - Oro: GC=F
    - Petróleo WTI: CL=F
    - Café: KC=F

    ### Indicadores

    - Rendimiento acumulado.
    - Volatilidad anualizada.
    - Precio máximo y mínimo.
    - Precios iniciales y finales.

    ### Fórmulas

    Rendimiento acumulado:

    (Precio final / Precio inicial) - 1

    Volatilidad anualizada:

    Desviación estándar de rendimientos diarios × raíz de 252.
    """)

    st.subheader("Verificación de datos")

    for nombre, df in datos.items():

        st.write(f"**{nombre}**")

        st.write(
            f"Registros: {len(df)} | "
            f"Desde: {df['Date'].min()} | "
            f"Hasta: {df['Date'].max()}"
        )

        st.download_button(
            f"Descargar CSV de {nombre}",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name=f"{nombre.replace(' ', '_')}.csv",
            mime="text/csv",
            key=f"descargar_{nombre}"
        )

st.divider()

st.caption(
    "APP FINANCIERA MALEJA | Ingeniería Financiera | ITM 2026"
)
