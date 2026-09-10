import pandas as pd
import plotly.express as px
import streamlit as st

from metrics import build_lead_time_dataframe
from zoho_api import get_all_pipeline_records, get_related_lists, get_stage_history_bulk

st.set_page_config(page_title="Bigin — Dashboard", layout="wide")
st.title("📊 Dashboard de Zoho Bigin")

with st.sidebar:
    st.header("Configuración")
    fields_input = st.text_input(
        "Campos a traer (separados por coma)",
        value="Deal_Name,Amount,Stage,Closing_Date,Created_Time",
        help="Deben coincidir con los api_name reales de tu módulo Pipelines. "
             "Podés confirmarlos en la pestaña 'Debug / metadata'.",
    )
    fields = [f.strip() for f in fields_input.split(",") if f.strip()]
    cargar = st.button("🔄 Cargar / refrescar datos")

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
        "Todavía no hay datos cargados. Completá tu archivo .env "
        "(ver .env.example) y tocá 'Cargar / refrescar datos'."
    )
    st.stop()

tab_overview, tab_leadtime, tab_debug = st.tabs(
    ["Vista general del pipeline", "Tiempo entre fases", "Debug / metadata"]
)

# ---------- Vista general ----------
with tab_overview:
    st.subheader("Deals por etapa")
    if "Stage" in deals_df.columns:
        conteo = deals_df["Stage"].value_counts().reset_index()
        conteo.columns = ["Etapa", "Cantidad"]
        fig = px.funnel(conteo, x="Cantidad", y="Etapa", title="Embudo de etapas")
        st.plotly_chart(fig, use_container_width=True)

        if "Amount" in deals_df.columns:
            monto_por_etapa = deals_df.groupby("Stage")["Amount"].sum().reset_index()
            fig2 = px.bar(monto_por_etapa, x="Stage", y="Amount", title="Monto total por etapa")
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.warning("No encontré la columna 'Stage' en los datos traídos.")

    st.dataframe(deals_df, use_container_width=True)

# ---------- Tiempo entre fases ----------
with tab_leadtime:
    st.subheader("Tiempo entre dos fases (usa Stage_History)")

    etapas_disponibles = (
        sorted(deals_df["Stage"].dropna().unique()) if "Stage" in deals_df.columns else []
    )

    if not etapas_disponibles:
        st.warning("Necesito la columna 'Stage' cargada para poder elegir fases.")
    else:
        col1, col2 = st.columns(2)
        stage_origen = col1.selectbox("Fase origen", etapas_disponibles, index=0)
        stage_destino = col2.selectbox(
            "Fase destino", etapas_disponibles, index=len(etapas_disponibles) - 1
        )

        if st.button("Calcular tiempos"):
            with st.spinner("Consultando Stage_History de cada trato (puede tardar)..."):
                ids = deals_df["id"].tolist()
                historial = get_stage_history_bulk(ids)
                lt_df = build_lead_time_dataframe(deals_df, historial, stage_origen, stage_destino)
            st.session_state.lt_df = lt_df

        if "lt_df" in st.session_state:
            lt_df = st.session_state.lt_df
            st.dataframe(lt_df, use_container_width=True)

            completados = lt_df[lt_df["estado"] == "completado"]
            if not completados.empty:
                fig3 = px.histogram(
                    completados, x="dias", nbins=20,
                    title=f"Distribución de días: {stage_origen} → {stage_destino}",
                )
                st.plotly_chart(fig3, use_container_width=True)
                c1, c2 = st.columns(2)
                c1.metric("Promedio de días", round(completados["dias"].mean(), 1))
                c2.metric("Mediana de días", round(completados["dias"].median(), 1))

            en_progreso = lt_df[lt_df["estado"] == "En progreso"]
            if not en_progreso.empty:
                st.warning(
                    f"{len(en_progreso)} tratos todavía no llegaron a '{stage_destino}'."
                )
                st.dataframe(en_progreso, use_container_width=True)

# ---------- Debug ----------
with tab_debug:
    st.subheader("Metadata para verificar nombres de campos y related lists")
    st.caption(
        "Usá esto para confirmar el api_name exacto de 'Stage History' y de "
        "cada campo en tu instancia (pueden variar si el layout es custom)."
    )
    if st.button("Consultar related lists del módulo Pipelines"):
        try:
            st.json(get_related_lists())
        except Exception as e:
            st.error(str(e))
