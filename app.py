import streamlit as st
import pandas as pd
import numpy as np
import ml_report as ml

st.set_page_config(
    layout="wide",
    page_title="Mercado Livre Ads – Relatório Estratégico"
)

# =========================
# Helpers
# =========================

def safe_for_streamlit(df):
    if df is None or not isinstance(df, pd.DataFrame):
        return pd.DataFrame()

    out = df.copy()
    out.columns = [str(c) for c in out.columns]
    out = out.replace([np.inf, -np.inf], np.nan)
    out = out.reset_index(drop=True)

    for c in out.columns:
        if out[c].dtype == "object":
            out[c] = out[c].astype(str)

    return out


# =========================
# UI
# =========================

st.title("📊 Mercado Livre Ads – Relatório Estratégico")

st.markdown(
    "Faça upload do **Relatório de Campanhas** para gerar a análise estratégica."
)

camp_file = st.file_uploader(
    "Relatório de Campanhas (Excel ou CSV)",
    type=["xlsx", "csv"]
)

if camp_file is None:
    st.info("Aguardando upload do relatório de campanhas.")
    st.stop()

# =========================
# Load & Process
# =========================

if camp_file.name.endswith(".csv"):
    camp = pd.read_csv(camp_file)
else:
    camp = pd.read_excel(camp_file)

camp = ml.enrich_campaign_metrics(camp)
camp = ml.classify_quadrants(camp)

# =========================
# Seletor de Plano
# =========================

plano_dias = st.selectbox(
    "Horizonte do plano de ação",
    options=[7, 15],
    index=0
)

camp = ml.estimate_impact(camp, horizon_days=int(plano_dias))
plan_df = ml.build_plan(camp, days=int(plano_dias))

# =========================
# Rankings
# =========================

ranks = ml.rank_campanhas(camp)

# =========================
# Dashboard
# =========================

st.subheader("📌 Matriz de Oportunidade")
st.dataframe(
    safe_for_streamlit(
        camp[
            ["Nome", "Quadrante", "Receita", "Investimento", "ROAS", "Impacto_R$", "Ação"]
        ]
    ),
    use_container_width=True
)

st.subheader("💰 Impacto Financeiro Estimado")
st.metric(
    "Impacto total estimado",
    f"R$ {camp['Impacto_R$'].sum():,.2f}"
)

st.subheader("🔥 Top 10 Melhores Campanhas")
st.dataframe(
    safe_for_streamlit(
        ranks["best"][
            ["Nome", "Receita", "Investimento", "ROAS", "Lucro_proxy"]
        ]
    ),
    use_container_width=True
)

st.subheader("🚨 Top 10 Piores Campanhas")
st.dataframe(
    safe_for_streamlit(
        ranks["worst"][
            ["Nome", "Receita", "Investimento", "ROAS", "Lucro_proxy"]
        ]
    ),
    use_container_width=True
)

st.subheader(f"🗓️ Plano de Ação – {plano_dias} dias")
st.dataframe(
    safe_for_streamlit(plan_df),
    use_container_width=True
)
