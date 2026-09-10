import pandas as pd
import plotly.express as px
import streamlit as st

from metrics import build_lead_time_dataframe
from zoho_api import get_all_pipeline_records, get_related_lists, get_stage_history_bulk

# ---------------------------------------------------------------------------
# Paleta P360 (misma identidad que los decks: azul monocromático)
# ---------------------------------------------------------------------------
PRIMARY = "#004DFC"
PRIMARY_INK = "#0038BA"
PRIMARY_50 = "#F1F5FF"
PRIMARY_100 = "#E5EDFF"
PRIMARY_200 = "#D9E4FF"
PRIMARY_300 = "#B8C9F8"
PRIMARY_400 = "#7DB7FF"
PRIMARY_500 = "#2A7FFF"
PRIMARY_700 = "#0038BA"
PRIMARY_900 = "#0B1A47"
BG = "#F6F9FF"
INK = "#101A33"
MUTED = "#607095"
CARD = "#FFFFFF"
WARN = "#D97706"

ESCALA_AZUL = [PRIMARY_300, PRIMARY_400, PRIMARY_500, PRIMARY, PRIMARY_INK, PRIMARY_900]

st.set_page_config(page_title="Bigin — Dashboard", page_icon=None, layout="wide")

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap');

    html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}

    .stApp {{ background-color: {BG}; }}

    .eyebrow {{
        font-family: 'JetBrains Mono', monospace;
        text-transform: uppercase;
        letter-spacing: 2.4px;
        font-size: 0.72rem;
        font-weight: 700;
        color: {PRIMARY_700};
        margin-bottom: 2px;
    }}
    .section-title {{
        font-weight: 800;
        color: {INK};
        font-size: 1.55rem;
        margin-top: 0;
        margin-bottom: 0.4rem;
    }}
    .section-block {{ margin-top: 2.2rem; margin-bottom: 0.6rem; }}

    div[data-testid="stMetric"] {{
        background-color: {CARD};
        border: 1px solid {PRIMARY_200};
        border-radius: 14px;
        padding: 16px 18px 10px 18px;
    }}
    div[data-testid="stMetricLabel"] {{
        font-family: 'JetBrains Mono', monospace;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        font-size: 0.68rem;
        font-weight: 700;
        color: {PRIMARY_700};
    }}
    div[data-testid="stMetricValue"] {{ color: {INK}; font-weight: 800; }}

    .block-container {{ padding-top: 2rem; }}
    hr {{ border-color: {PRIMARY_200}; }}
    </style>
    """,
    unsafe_allow_html=True,
)


def section(eyebrow: str, title: str):
    st.markdown(
        f"""
        <div class="section-block">
            <div class="eyebrow">{eyebrow}</div>
            <div class="section-title">{title}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.markdown(f'<div class="eyebrow">PAGOS360 · CRM ANALYTICS</div>', unsafe_allow_html=True)
st.markdown(
    f'<h1 style="color:{INK}; font-weight:800; margin-top:2px;">Dashboard de Zoho Bigin</h1>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar / carga de datos
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f'<div class="eyebrow">Configuración</div>', unsafe_allow_html=True)
    fields_input = st.text_input(
        "Campos a traer (separados por coma)",
        value="Deal_Name,Amount,Stage,Sub_Pipeline,Closing_Date,Created_Time",
        help="Deben coincidir con los api_name reales de tu módulo Pipelines. "
             "Confirmalos en 'Debug / metadata', abajo de todo.",
    )
    fields = [f.strip() for f in fields_input.split(",") if f.strip()]

    pipeline_field = st.text_input(
        "Campo que identifica el Pipeline",
        value="Sub_Pipeline",
        help="Nombre del campo que distingue distintos pipelines dentro de tu cuenta "
             "(a veces se llama 'Sub_Pipeline' o 'Pipeline'). Dejalo vacío si no aplica.",
    ).strip()

    cargar = st.button("Cargar / refrescar datos", use_container_width=True)

if "deals_df" not in st.session_state:
    st.session_state.deals_df = pd.DataFrame()

if cargar:
    with st.spinner("Consultando Bigin..."):
        try:
            st.session_state.deals_df = get_all_pipeline_records(fields)
        except Exception as e:
            st.error(f"Error al traer los datos: {e}")

deals_df = st.session_state.deals_df

if deals_df.empty:
    st.info(
        "Todavía no hay datos cargados. Completá tu archivo .env / Secrets "
        "y tocá 'Cargar / refrescar datos' en la barra lateral."
    )
    st.stop()

tiene_pipeline_field = bool(pipeline_field) and pipeline_field in deals_df.columns

# ---------------------------------------------------------------------------
# 1. Conteo de oportunidades (por pipeline)
# ---------------------------------------------------------------------------
section("01 · Volumen", "Conteo de oportunidades por pipeline")

total_deals = len(deals_df)
total_amount = deals_df["Amount"].sum() if "Amount" in deals_df.columns else None
n_pipelines = deals_df[pipeline_field].nunique() if tiene_pipeline_field else None

k1, k2, k3 = st.columns(3)
k1.metric("Total de oportunidades", f"{total_deals:,}")
if total_amount is not None:
    k2.metric("Monto total", f"${total_amount:,.0f}")
if n_pipelines is not None:
    k3.metric("Pipelines distintos", n_pipelines)

if tiene_pipeline_field:
    conteo_pipe = deals_df[pipeline_field].fillna("Sin pipeline").value_counts().reset_index()
    conteo_pipe.columns = ["Pipeline", "Cantidad"]
    conteo_pipe = conteo_pipe.sort_values("Cantidad", ascending=True)

    fig_pipe = px.bar(
        conteo_pipe, x="Cantidad", y="Pipeline", orientation="h",
        color="Cantidad", color_continuous_scale=ESCALA_AZUL,
        text="Cantidad",
    )
    fig_pipe.update_traces(textposition="outside")
    fig_pipe.update_layout(
        showlegend=False, coloraxis_showscale=False,
        margin=dict(t=10, b=10), height=max(220, 40 * len(conteo_pipe)),
        xaxis_title="", yaxis_title="", plot_bgcolor=CARD, paper_bgcolor=CARD,
    )
    st.plotly_chart(fig_pipe, use_container_width=True)

    pipelines_disponibles = ["Todos"] + sorted(deals_df[pipeline_field].dropna().unique().tolist())
else:
    st.caption(
        f"No encontré el campo '{pipeline_field}' en los datos traídos — "
        "revisá el nombre en la barra lateral o en 'Debug / metadata'."
    )
    pipelines_disponibles = ["Todos"]

pipeline_elegido = (
    st.selectbox("Filtrar el resto del panel por pipeline", pipelines_disponibles)
    if len(pipelines_disponibles) > 1
    else "Todos"
)

if pipeline_elegido != "Todos" and tiene_pipeline_field:
    deals_filtrado = deals_df[deals_df[pipeline_field] == pipeline_elegido]
else:
    deals_filtrado = deals_df

# ---------------------------------------------------------------------------
# 2. Desglose de fases por pipeline
# ---------------------------------------------------------------------------
section("02 · Distribución", f"Desglose de fases{'' if pipeline_elegido == 'Todos' else f' — {pipeline_elegido}'}")

if "Stage" in deals_filtrado.columns:
    conteo_stage = deals_filtrado["Stage"].value_counts().reset_index()
    conteo_stage.columns = ["Etapa", "Cantidad"]
    conteo_stage = conteo_stage.sort_values("Cantidad", ascending=True)

    fig_stage = px.bar(
        conteo_stage, x="Cantidad", y="Etapa", orientation="h",
        color="Cantidad", color_continuous_scale=ESCALA_AZUL,
        text="Cantidad",
    )
    fig_stage.update_traces(textposition="outside")
    fig_stage.update_layout(
        showlegend=False, coloraxis_showscale=False,
        margin=dict(t=10, b=10), height=max(320, 32 * len(conteo_stage)),
        xaxis_title="", yaxis_title="", plot_bgcolor=CARD, paper_bgcolor=CARD,
    )
    st.plotly_chart(fig_stage, use_container_width=True)
else:
    st.warning("No encontré la columna 'Stage' en los datos traídos.")

with st.expander("Ver tabla completa de oportunidades"):
    st.dataframe(deals_filtrado, use_container_width=True)

# ---------------------------------------------------------------------------
# 3. Tiempo entre fases (promedio de días)
# ---------------------------------------------------------------------------
section("03 · Velocidad", "Cantidad de días entre fases")
st.caption("Calculado a partir del historial real de cada trato (Stage_History).")

etapas_disponibles = (
    sorted(deals_filtrado["Stage"].dropna().unique()) if "Stage" in deals_filtrado.columns else []
)

if not etapas_disponibles:
    st.warning("Necesito la columna 'Stage' cargada para poder elegir fases.")
else:
    col1, col2, col3 = st.columns([2, 2, 1])
    stage_origen = col1.selectbox("Fase origen", etapas_disponibles, index=0, key="origen")
    stage_destino = col2.selectbox(
        "Fase destino", etapas_disponibles, index=len(etapas_disponibles) - 1, key="destino"
    )
    col3.write("")
    col3.write("")
    calcular = col3.button("Calcular tiempos", use_container_width=True)

    if calcular:
        with st.spinner("Consultando Stage_History de cada trato (puede tardar)..."):
            ids = deals_filtrado["id"].tolist()
            historial = get_stage_history_bulk(ids)
            lt_df = build_lead_time_dataframe(deals_filtrado, historial, stage_origen, stage_destino)
        st.session_state.lt_df = lt_df
        st.session_state.lt_stages = (stage_origen, stage_destino)

    if "lt_df" in st.session_state:
        lt_df = st.session_state.lt_df
        o, d = st.session_state.get("lt_stages", (stage_origen, stage_destino))

        completados = lt_df[lt_df["estado"] == "completado"]
        en_progreso = lt_df[lt_df["estado"] == "En progreso"]
        sin_dato = lt_df[lt_df["estado"] == "sin_dato"]

        st.markdown(
            f'<div class="eyebrow" style="margin-top:10px;">{o} → {d}</div>',
            unsafe_allow_html=True,
        )

        m1, m2, m3, m4 = st.columns(4)
        if not completados.empty:
            m1.metric("Promedio de días", round(completados["dias"].mean(), 1))
            m2.metric("Mediana de días", round(completados["dias"].median(), 1))
        m3.metric("Completados", len(completados))
        m4.metric("En progreso", len(en_progreso))

        if not completados.empty:
            fig3 = px.histogram(
                completados, x="dias", nbins=20,
                color_discrete_sequence=[PRIMARY],
            )
            fig3.update_layout(
                title=f"Distribución de días — {o} → {d}",
                xaxis_title="Días", yaxis_title="Cantidad de oportunidades",
                margin=dict(t=50, b=10), height=380,
                plot_bgcolor=CARD, paper_bgcolor=CARD,
            )
            st.plotly_chart(fig3, use_container_width=True)

        tab_c, tab_p, tab_s = st.tabs([
            f"Completados ({len(completados)})",
            f"En progreso ({len(en_progreso)})",
            f"Sin datos ({len(sin_dato)})",
        ])
        with tab_c:
            st.dataframe(completados, use_container_width=True)
        with tab_p:
            st.dataframe(en_progreso, use_container_width=True)
        with tab_s:
            st.caption("Oportunidades que nunca pasaron por la fase origen elegida.")
            st.dataframe(sin_dato, use_container_width=True)

# ---------------------------------------------------------------------------
# Debug (utilidad, no forma parte del flujo principal)
# ---------------------------------------------------------------------------
with st.expander("Debug / metadata (nombres reales de campos)"):
    st.caption(
        "Usá esto para confirmar el api_name exacto de 'Stage History' y de "
        "cada campo en tu instancia (pueden variar si el layout es custom)."
    )
    colA, colB = st.columns(2)
    if colA.button("Consultar related lists del módulo Pipelines"):
        try:
            st.json(get_related_lists())
        except Exception as e:
            st.error(str(e))
    if colB.button("Consultar campos del módulo Pipelines (buscar el campo Pipeline)"):
        try:
            from zoho_api import get_fields_metadata
            data = get_fields_metadata()
            resumen = [
                {"api_name": f.get("api_name"), "label": f.get("field_label")}
                for f in data.get("fields", [])
            ]
            st.dataframe(pd.DataFrame(resumen), use_container_width=True)
        except Exception as e:
            st.error(str(e))
