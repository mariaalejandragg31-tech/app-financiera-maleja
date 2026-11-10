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


/* Texto general del menú lateral */
[data-testid="stSidebar"] {
    background-color: #172438;
    color: #FFFFFF;
}

/* Títulos y etiquetas del menú */
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] p {
    color: #FFFFFF !important;
}

/* Campos de selección de fechas */
[data-testid="stSidebar"] [data-testid="stDateInput"] input {
    background-color: #FFFFFF !important;
    color: #172438 !important;
    border: 1px solid #D6A84B !important;
    border-radius: 8px !important;
}

/* Iconos de calendario */
[data-testid="stSidebar"] [data-testid="stDateInput"] button {
    color: #172438 !important;
}

/* Calendario desplegable */
[data-testid="stDateInput"] [role="dialog"] {
    color: #172438 !important;
}

/* Valores de los controles */
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] select {
    color: #172438 !important;
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

        # Precios inicial y final
        precio_inicial = precios.iloc[0]
        precio_final = precios.iloc[-1]

        # Rendimiento acumulado
        rendimiento = (
            precio_final / precio_inicial - 1
        )

        # Volatilidad anualizada
        volatilidad = (
            rendimientos.std() * np.sqrt(252)
        )

        # Máximo drawdown
        maximos_acumulados = precios.cummax()

        drawdown = (
            precios / maximos_acumulados
        ) - 1

        max_drawdown = drawdown.min()

        resultados[nombre] = {

            "Precio inicial": precio_inicial,

            "Precio final": precio_final,

            "Rendimiento acumulado": rendimiento,

            "Volatilidad anualizada": volatilidad,

            "Máxima caída": max_drawdown,

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

    # ======================================
    # CONCLUSIONES FINANCIERAS AUTOMÁTICAS
    # ======================================

    st.divider()

    st.header("Conclusiones financieras")

    mayor_rendimiento = indicadores[
        "Rendimiento acumulado"
    ].idxmax()

    menor_rendimiento = indicadores[
        "Rendimiento acumulado"
    ].idxmin()

    mayor_volatilidad = indicadores[
        "Volatilidad anualizada"
    ].idxmax()

    menor_volatilidad = indicadores[
        "Volatilidad anualizada"
    ].idxmin()

    col1, col2 = st.columns(2)

    with col1:
        st.success(
            f"Mayor rendimiento histórico: {mayor_rendimiento} "
            f"({indicadores.loc[mayor_rendimiento, 'Rendimiento acumulado']:.2%})"
        )

        st.info(
            f"Menor rendimiento histórico: {menor_rendimiento} "
            f"({indicadores.loc[menor_rendimiento, 'Rendimiento acumulado']:.2%})"
        )

    with col2:
        st.warning(
            f"Mayor volatilidad: {mayor_volatilidad} "
            f"({indicadores.loc[mayor_volatilidad, 'Volatilidad anualizada']:.2%})"
        )

        st.info(
            f"Menor volatilidad: {menor_volatilidad} "
            f"({indicadores.loc[menor_volatilidad, 'Volatilidad anualizada']:.2%})"
        )

    st.subheader("Interpretación financiera")

    st.write(
        f"Durante el período seleccionado, {mayor_rendimiento} "
        "registró el mayor rendimiento acumulado de los activos "
        "analizados. Esto representa el mayor incremento relativo "
        "entre su precio inicial y final."
    )

    st.write(
        f"Por otra parte, {mayor_volatilidad} presentó la mayor "
        "volatilidad anualizada, lo que indica una mayor variabilidad "
        "histórica de sus rendimientos diarios."
    )

    st.write(
        f"{menor_volatilidad} presentó la menor volatilidad "
        "anualizada dentro del período estudiado."
    )

    st.caption(
        "Estas conclusiones describen exclusivamente el comportamiento "
        "histórico. No constituyen pronósticos ni recomendaciones "
        "de inversión."
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

        # =========================================
        # COMPARACION RIESGO Y RENDIMIENTO
        # =========================================

        st.divider()

        st.subheader("Relación riesgo y rendimiento")

        comparacion_riesgo = indicadores.reset_index()

        comparacion_riesgo = comparacion_riesgo.rename(
            columns={"index": "Commodity"}
        )

        figura_riesgo = px.scatter(
            comparacion_riesgo,
            x="Volatilidad anualizada",
            y="Rendimiento acumulado",
            color="Commodity",
            text="Commodity",
            size_max=20,
            title="Rendimiento acumulado frente a volatilidad"
        )

        figura_riesgo.update_layout(
            template="plotly_dark",
            title_x=0.5,
            height=500,
            xaxis_title="Volatilidad anualizada",
            yaxis_title="Rendimiento acumulado"
        )

        figura_riesgo.update_traces(
            textposition="top center"
        )

        st.plotly_chart(
            figura_riesgo,
            use_container_width=True
        )

        st.caption(
            "Cada punto representa un commodity. El gráfico "
            "permite comparar el rendimiento acumulado con "
            "la volatilidad anualizada del período."
        )

        # ======================================
        # MATRIZ COMPARATIVA FINANCIERA
        # ======================================

        st.divider()

        st.header("Matriz de resultados financieros")

        matriz = indicadores.copy()

        matriz.index.name = "Commodity"

        st.dataframe(
            matriz.style.format({
                "Precio inicial": "{:,.2f}",
                "Precio final": "{:,.2f}",
                "Rendimiento acumulado": "{:.2%}",
                "Volatilidad anualizada": "{:.2%}",
                "Máxima caída": "{:.2%}",
                "Precio máximo": "{:,.2f}",
                "Precio mínimo": "{:,.2f}"
            }),
            use_container_width=True
        )

        st.download_button(
            "Descargar matriz comparativa",
            data=matriz.to_csv().encode("utf-8"),
            file_name="matriz_financiera_maleja.csv",
            mime="text/csv",
            key="descargar_matriz"
        )

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

    st.subheader("Análisis de máxima caída")

    caidas = indicadores[
        ["Máxima caída"]
    ].reset_index()

    caidas.columns = [
        "Commodity",
        "Máxima caída"
    ]

    caidas["Caída (%)"] = (
        caidas["Máxima caída"] * 100
    )

    figura_caidas = px.bar(
        caidas,
        x="Commodity",
        y="Caída (%)",
        color="Commodity",
        title="Máxima caída histórica (Maximum Drawdown)",
        text="Caída (%)"
    )

    figura_caidas.update_layout(
        template="plotly_dark",
        title_x=0.5,
        height=450
    )

    st.plotly_chart(
        figura_caidas,
        use_container_width=True
    )

    # =========================================
    # VOLATILIDAD MOVIL DE 30 DIAS
    # =========================================

    st.divider()

    st.subheader("Evolución de la volatilidad móvil")

    volatilidades_moviles = []

    for nombre, df in datos.items():

        serie = df[["Date", "Close"]].copy()

        serie = serie.sort_values("Date")

        serie["Rendimiento diario"] = (
            serie["Close"].pct_change()
        )

        serie["Volatilidad móvil"] = (
            serie["Rendimiento diario"]
            .rolling(window=30)
            .std() * np.sqrt(252) * 100
        )

        serie["Commodity"] = nombre

        volatilidades_moviles.append(
            serie[
                ["Date", "Volatilidad móvil", "Commodity"]
            ]
        )

    volatilidad_movil_df = pd.concat(
        volatilidades_moviles,
        ignore_index=True
    )

    figura_movil = px.line(
        volatilidad_movil_df,
        x="Date",
        y="Volatilidad móvil",
        color="Commodity",
        title="Volatilidad anualizada móvil de 30 días",
        labels={
            "Date": "Fecha",
            "Volatilidad móvil": "Volatilidad (%)",
            "Commodity": "Commodity"
        }
    )

    figura_movil.update_layout(
        template="plotly_dark",
        title_x=0.5,
        height=500,
        hovermode="x unified"
    )

    st.plotly_chart(
        figura_movil,
        use_container_width=True
    )

    st.caption(
        "La volatilidad móvil utiliza los últimos 30 "
        "rendimientos diarios disponibles y se anualiza "
        "con 252 días de negociación."
    )

    st.subheader("Resultados")

    
    st.dataframe(
        indicadores.style.format({
            "Rendimiento acumulado": "{:.2%}",
            "Volatilidad anualizada": "{:.2%}",
            "Máxima caída": "{:.2%}"
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
