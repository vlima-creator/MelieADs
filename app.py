import streamlit as st
from datetime import datetime
from io import BytesIO
import pandas as pd
import ml_report as ml

st.set_page_config(page_title="ML Ads - Relatorio Estrategico", layout="wide")
st.title("Mercado Livre Ads - Relatorio Estrategico")

# -----------------------------
# Helpers
# -----------------------------
def safe_for_streamlit(df: pd.DataFrame) -> pd.DataFrame:
    if df is None:
        return pd.DataFrame()
    out = df.copy()
    for c in out.columns:
        if out[c].dtype == "object":
            out[c] = out[c].astype(str)
    return out


def _safe_div(a, b):
    try:
        b = float(b)
        if b != 0:
            return float(a) / b
    except Exception:
        return 0.0
    return 0.0


def _money(v):
    try:
        return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def _pct(v):
    try:
        return f"{float(v) * 100:.2f}%".replace(".", ",")
    except Exception:
        return "0,00%"


def snapshot_to_bytes(meta: dict, camp_agg: pd.DataFrame, camp_strat: pd.DataFrame) -> bytes:
    out = BytesIO()
    meta_df = pd.DataFrame([meta])

    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        meta_df.to_excel(writer, index=False, sheet_name="META")
        (camp_agg if camp_agg is not None else pd.DataFrame()).to_excel(writer, index=False, sheet_name="CAMP_AGG")
        (camp_strat if camp_strat is not None else pd.DataFrame()).to_excel(writer, index=False, sheet_name="CAMP_STRAT")

    out.seek(0)
    return out.read()


def load_snapshot(snapshot_file):
    meta = pd.read_excel(snapshot_file, sheet_name="META")
    camp_agg_prev = pd.read_excel(snapshot_file, sheet_name="CAMP_AGG")
    camp_strat_prev = pd.read_excel(snapshot_file, sheet_name="CAMP_STRAT")
    return meta, camp_agg_prev, camp_strat_prev


def _sum_col(df, col):
    if df is None or df.empty or col not in df.columns:
        return 0.0
    return float(pd.to_numeric(df[col], errors="coerce").fillna(0).sum())


def _nunique_col(df, col):
    if df is None or df.empty or col not in df.columns:
        return 0
    return int(df[col].nunique())


# -----------------------------
# Inputs
# -----------------------------
modo = st.radio(
    "Selecione o tipo de relatorio de campanhas que voce exportou:",
    ["CONSOLIDADO (decisao)", "DIARIO (monitoramento)"],
    horizontal=True
)
modo_key = "consolidado" if "CONSOLIDADO" in modo else "diario"

with st.expander("Regras (ajustaveis)"):
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        enter_visitas_min = st.number_input("ENTRAR: Visitas min.", min_value=0, value=50, step=10)
    with c2:
        enter_conv_pct = st.number_input("ENTRAR: Conversao organica min. (%)", min_value=0.0, value=5.0, step=0.5)
    with c3:
        pause_invest_min = st.number_input("PAUSAR: Investimento min. (R$)", min_value=0.0, value=100.0, step=50.0)
    with c4:
        pause_cvr_pct = st.number_input("PAUSAR: CVR max. (%)", min_value=0.0, value=1.0, step=0.2)

st.divider()

cA, cB, cC = st.columns(3)
with cA:
    period_label = st.text_input("Rotulo do periodo (opcional)", value="Periodo atual")
with cB:
    plano_dias = st.selectbox("Plano de acao (dias)", options=[7, 14, 15], index=0)
with cC:
    topn_rank = st.selectbox("Rankings (Top N)", options=[5, 10, 20], index=1)

st.divider()

u1, u2, u3 = st.columns(3)
with u1:
    organico_file = st.file_uploader("Relatorio organico (publicacoes) (opcional, recomendado para TACOS)", type=["xlsx"])
with u2:
    campanhas_file = st.file_uploader("Relatorio campanhas Ads", type=["xlsx", "csv"])
with u3:
    patrocinados_file = st.file_uploader("Relatorio anuncios patrocinados", type=["xlsx", "csv"])

st.subheader("Historico comparativo (opcional)")
st.caption("Recomendado: use o snapshot padrao do app como periodo anterior.")
snapshot_prev_file = st.file_uploader("Snapshot do periodo anterior (Excel do app)", type=["xlsx"])

if not (campanhas_file and patrocinados_file):
    st.info("Envie pelo menos Campanhas e Anuncios Patrocinados para liberar o dashboard.")
    st.stop()

# -----------------------------
# Load + Build
# -----------------------------
with st.spinner("Lendo arquivos..."):
    org = pd.DataFrame()
    if organico_file is not None:
        org = ml.load_organico(organico_file)

    pat = ml.load_patrocinados(patrocinados_file)
    if modo_key == "diario":
        camp = ml.load_campanhas_diario(campanhas_file)
    else:
        camp = ml.load_campanhas_consolidado(campanhas_file)

camp_agg = ml.build_campaign_agg(camp, modo_key)

kpis, pause, enter, scale, acos, camp_strat = ml.build_tables(
    org, camp_agg, pat,
    enter_visitas_min=int(enter_visitas_min),
    enter_conv_min=float(enter_conv_pct) / 100.0,
    pause_invest_min=float(pause_invest_min),
    pause_cvr_max=float(pause_cvr_pct) / 100.0,
)

daily = None
if modo_key == "diario":
    daily = ml.build_daily_from_diario(camp)

diagnosis = ml.build_executive_diagnosis(camp_strat, daily=daily)
panel = ml.build_control_panel(camp_strat)
high = ml.build_opportunity_highlights(camp_strat)

# plano dinamico (7, 14, 15)
plan_df = ml.build_plan(camp_strat, days=int(plano_dias))

# -----------------------------
# KPIs sempre do camp_agg
# -----------------------------
inv_ads = _sum_col(camp_agg, "Investimento")
rev_ads = _sum_col(camp_agg, "Receita")
vendas_ads = _sum_col(camp_agg, "Vendas")
camp_unicas = _nunique_col(camp_agg, "Nome")
ids_patro = ml.count_unique_ad_ids(pat)

roas = _safe_div(rev_ads, inv_ads)
acos_ref = _safe_div(inv_ads, rev_ads)

# -----------------------------
# TACOS
# -----------------------------
tacos_overall = None
tacos_prod_best = pd.DataFrame()
tacos_prod_worst = pd.DataFrame()
tacos_camp_best = pd.DataFrame()
tacos_camp_worst = pd.DataFrame()
tacos_camp_col = None

if organico_file is not None and org is not None and not org.empty:
    tacos_overall = ml.compute_tacos_overall_from_org(camp_agg, org)

    res_prod = ml.compute_tacos_by_product(org, pat, top_n=int(topn_rank))
    tacos_prod_best = res_prod.get("best", pd.DataFrame())
    tacos_prod_worst = res_prod.get("worst", pd.DataFrame())

    res_camp = ml.compute_tacos_by_campaign(org, pat, top_n=int(topn_rank))
    tacos_camp_best = res_camp.get("best", pd.DataFrame())
    tacos_camp_worst = res_camp.get("worst", pd.DataFrame())
    tacos_camp_col = res_camp.get("campaign_col")

# -----------------------------
# Snapshot (download) + Comparative
# -----------------------------
snapshot_meta = {
    "period_label": period_label,
    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "modo": modo_key,
}

snapshot_bytes = snapshot_to_bytes(snapshot_meta, camp_agg, camp_strat)

prev_meta = None
camp_agg_prev = None
camp_strat_prev = None
if snapshot_prev_file is not None:
    try:
        prev_meta, camp_agg_prev, camp_strat_prev = load_snapshot(snapshot_prev_file)
    except Exception:
        prev_meta, camp_agg_prev, camp_strat_prev = None, None, None

# -----------------------------
# UI
# -----------------------------
tab1, tab2 = st.tabs(["Dashboard", "Gerar Excel"])

with tab1:
    st.subheader("Diagnostico Executivo")
    st.write(f"ROAS da conta: **{diagnosis['ROAS']:.2f}** | ACOS real: **{diagnosis['ACOS_real']:.2f}**")
    st.write(f"Veredito: **{diagnosis['Veredito']}**")

    t = diagnosis.get("Tendencias", {})
    if t and t.get("cpc_proxy_up") is not None:
        st.caption(
            f"Tendencias (ultimos 7d vs 7d anteriores) | "
            f"CPC proxy: {t['cpc_proxy_up']:+.1%} | "
            f"Ticket: {t['ticket_down']:+.1%} | "
            f"ROAS: {t['roas_down']:+.1%}"
        )

    st.divider()
    st.subheader("KPIs (Ads)")
    a, b, c, d, e, f = st.columns(6)
    a.metric("Investimento", _money(inv_ads))
    b.metric("Receita Ads", _money(rev_ads))
    c.metric("Vendas Ads", int(vendas_ads))
    d.metric("ROAS", f"{float(roas):.2f}")
    e.metric("Campanhas unicas", int(camp_unicas))
    f.metric("IDs patrocinados", int(ids_patro))

    st.divider()
    st.subheader("TACOS (saude geral)")
    if organico_file is None:
        st.info("Para TACOS, envie o relatorio organico (publicacoes).")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Faturamento total estimado", _money(tacos_overall.get("Faturamento_total_estimado", 0)))
        c2.metric("TACOS (conta)", _pct(tacos_overall.get("TACOS_conta", 0)))
        c3.metric("ACOS (referencia)", _pct(acos_ref))
        st.caption("TACOS usa faturamento total (organico + pago). ACOS usa apenas receita de Ads.")

    st.divider()
    st.subheader("Matriz de Oportunidade (Destaques)")
    cX, cY = st.columns(2)
    with cX:
        st.write("Locomotivas (CPI 80% + perda por classificacao)")
        st.dataframe(safe_for_streamlit(high.get("Locomotivas", pd.DataFrame())), use_container_width=True)
    with cY:
        st.write("Minas Limitadas (ROAS alto + perda por orcamento)")
        st.dataframe(safe_for_streamlit(high.get("Minas", pd.DataFrame())), use_container_width=True)

    st.divider()
    st.subheader(f"Plano de Acao - {plano_dias} dias")
    st.dataframe(safe_for_streamlit(plan_df), use_container_width=True)

    st.divider()
    st.subheader("Painel de Controle Geral")
    st.dataframe(safe_for_streamlit(panel), use_container_width=True)

    st.divider()
    cM, cN = st.columns(2)
    with cM:
        st.subheader("Campanhas para PAUSAR ou REVISAR")
        st.dataframe(safe_for_streamlit(pause), use_container_width=True)
    with cN:
        st.subheader("Anuncios para ENTRAR em Ads (organico forte)")
        st.dataframe(safe_for_streamlit(enter), use_container_width=True)

    if organico_file is not None:
        st.divider()
        st.subheader("Rankings TACOS (Top N)")
        if tacos_prod_best is not None and not tacos_prod_best.empty:
            st.write(f"Top {topn_rank} melhores produtos por TACOS (menor TACOS)")
            st.dataframe(safe_for_streamlit(tacos_prod_best), use_container_width=True)

        if tacos_prod_worst is not None and not tacos_prod_worst.empty:
            st.write(f"Top {topn_rank} piores produtos por TACOS (maior TACOS)")
            st.dataframe(safe_for_streamlit(tacos_prod_worst), use_container_width=True)

        if tacos_camp_col is None:
            st.info("TACOS por campanha depende de uma coluna de campanha no relatorio de patrocinados.")
        else:
            if tacos_camp_best is not None and not tacos_camp_best.empty:
                st.write(f"Top {topn_rank} melhores campanhas por TACOS")
                st.dataframe(safe_for_streamlit(tacos_camp_best), use_container_width=True)
            if tacos_camp_worst is not None and not tacos_camp_worst.empty:
                st.write(f"Top {topn_rank} piores campanhas por TACOS")
                st.dataframe(safe_for_streamlit(tacos_camp_worst), use_container_width=True)

    st.divider()
    st.subheader("Snapshot e comparativo")
    st.download_button(
        "Baixar snapshot do periodo (padrao do app)",
        data=snapshot_bytes,
        file_name=f"snapshot_{datetime.now().strftime('%Y-%m-%d_%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    if camp_agg_prev is not None and isinstance(camp_agg_prev, pd.DataFrame) and not camp_agg_prev.empty:
        st.divider()
        st.subheader("Comparativo vs periodo anterior")

        invest_prev = _sum_col(camp_agg_prev, "Investimento")
        rec_prev = _sum_col(camp_agg_prev, "Receita")
        roas_prev = _safe_div(rec_prev, invest_prev)
        acos_prev = _safe_div(invest_prev, rec_prev)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Investimento", _money(inv_ads), delta=_money(inv_ads - invest_prev))
        c2.metric("Receita Ads", _money(rev_ads), delta=_money(rev_ads - rec_prev))
        c3.metric("ROAS", f"{roas:.2f}", delta=f"{(roas - roas_prev):+.2f}")
        c4.metric("ACOS", _pct(acos_ref), delta=f"{(acos_ref - acos_prev) * 100:+.2f}%".replace(".", ","))

with tab2:
    st.subheader("Gerar relatorio final (Excel)")
    if st.button("Gerar e baixar Excel"):
        with st.spinner("Gerando Excel..."):
            bytes_xlsx = ml.gerar_excel(kpis, camp_agg, pause, enter, scale, acos, camp_strat, daily=daily)

        nome = f"Relatorio_ML_ADs_Estrategico_{datetime.now().strftime('%Y-%m-%d_%H%M')}.xlsx"
        st.download_button(
            "Baixar Excel",
            data=bytes_xlsx,
            file_name=nome,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        st.success("OK")
