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
    """Evita erro do pyarrow no st.dataframe quando há colunas com tipos mistos."""
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
    """Snapshot padrão do app para histórico comparativo."""
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


def _detect_pat_id_col(pat: pd.DataFrame):
    if pat is None or pat.empty:
        return None
    for cand in ["ID do anúncio", "Id do anúncio", "id_anuncio", "ID", "Anuncio ID", "ID do anuncio", "Id do anuncio"]:
        if cand in pat.columns:
            return cand
    return None


def _campaign_col_from_pat(pat: pd.DataFrame):
    if pat is None or pat.empty:
        return None
    for cand in ["Nome da campanha", "Campanha", "Campaign", "campaign_name", "nome_campanha"]:
        if cand in pat.columns:
            return cand
    return None


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
    campanhas_file = st.file_uploader("Relatorio campanhas Ads", type=["xlsx"])
with u3:
    patrocinados_file = st.file_uploader("Relatorio anuncios patrocinados", type=["xlsx"])

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
    camp = ml.load_campanhas_diario(campanhas_file) if modo_key == "diario" else ml.load_campanhas_consolidado(campanhas_file)

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

# plano dinamico
if hasattr(ml, "build_plan"):
    plan_df = ml.build_plan(camp_strat, days=int(plano_dias))
else:
    plan_df = ml.build_7_day_plan(camp_strat)


# -----------------------------
# KPIs (AGORA SEMPRE VINDO DO camp_agg e pat)
# -----------------------------
inv_ads = _sum_col(camp_agg, "Investimento")
rev_ads = _sum_col(camp_agg, "Receita")
vendas_ads = _sum_col(camp_agg, "Vendas")
camp_unicas = _nunique_col(camp_agg, "Nome")

id_col = _detect_pat_id_col(pat)
ids_patro = int(pat[id_col].nunique()) if (id_col and pat is not None and not pat.empty) else 0

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
    if hasattr(ml, "compute_tacos_overall_from_org"):
        try:
            tacos_overall = ml.compute_tacos_overall_from_org(camp_agg, org)
        except Exception:
            tacos_overall = None

    if hasattr(ml, "compute_tacos_by_product"):
        try:
            res = ml.compute_tacos_by_product(org, pat, top_n=int(topn_rank))
            tacos_prod_best = res.get("best", pd.DataFrame())
            tacos_prod_worst = res.get("worst", pd.DataFrame())
        except Exception:
            pass

    if hasattr(ml, "compute_tacos_by_campaign"):
        try:
            res = ml.compute_tacos_by_campaign(org, pat, top_n=int(topn_rank))
            tacos_camp_best = res.get("best", pd.DataFrame())
            tacos_camp_worst = res.get("worst", pd.DataFrame())
            tacos_camp_col = res.get("campaign_col")
        except Exception:
            pass

    # Se o ml_report ainda nao retorna campaign_col, tenta detectar aqui
    if tacos_camp_col is None:
        tacos_camp_col = _campaign_col_from_pat(pat)


# -----------------------------
# Snapshot (download) + Comparative
# -----------------------------
snapshot_meta = {
    "period_label": period_label,
    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "modo": modo_key,
}

if hasattr(ml, "generate_snapshot_excel"):
    try:
        snapshot_bytes = ml.generate_snapshot_excel(
            camp_agg=camp_agg,
            camp_strat=camp_strat,
            period_label=period_label,
            start_date="",
            end_date="",
        )
    except Exception:
        snapshot_bytes = snapshot_to_bytes(snapshot_meta, camp_agg, camp_strat)
else:
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
    if t and (t.get("cpc_proxy_up") is not None):
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
        st.info("Para TACOS (conta, produto e campanha), envie o relatorio organico (publicacoes).")
    else:
        if tacos_overall is not None:
            c1, c2, c3 = st.columns(3)
            c1.metric("Faturamento total estimado", _money(tacos_overall.get("Faturamento_total_estimado")))
            c2.metric("TACOS (conta)", _pct(tacos_overall.get("TACOS_conta")))
            c3.metric("ACOS (referencia)", _pct(acos_ref))
            st.caption("TACOS usa faturamento total (organico + pago). ACOS usa apenas receita de Ads.")
        else:
            st.warning("Nao consegui calcular TACOS (verifique o relatorio organico).")

    st.divider()

    if modo_key == "diario" and daily is not None and not daily.empty:
        st.subheader("Evolucao diaria")
        daily2 = daily.copy()
        if "Desde" in daily2.columns:
            daily2 = daily2.set_index("Desde")
        cols = [c for c in ["Investimento", "Receita", "Vendas"] if c in daily2.columns]
        if cols:
            st.line_chart(daily2[cols])

        st.divider()

    st.subheader("Top 10 campanhas por Receita")
    bar = camp_agg.copy()
    for col in ["Receita", "Investimento", "Vendas", "ROAS", "CVR"]:
        if col in bar.columns:
            bar[col] = pd.to_numeric(bar[col], errors="coerce")
    if "Receita" in bar.columns and "Nome" in bar.columns:
        bar = bar.sort_values("Receita", ascending=False).head(10).set_index("Nome")
        st.bar_chart(bar[["Receita"]])

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
        st.subheader("Campanhas para PAUSAR/REVISAR")
        st.dataframe(safe_for_streamlit(pause), use_container_width=True)
    with cN:
        st.subheader("Anuncios para ENTRAR em Ads (organico forte)")
        st.dataframe(safe_for_streamlit(enter), use_container_width=True)

    # Rankings TACOS
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
    st.subheader("Snapshot padrao e comparativo")

    st.download_button(
        "Baixar snapshot do periodo (padrao do app)",
        data=snapshot_bytes,
        file_name=f"snapshot_{datetime.now().strftime('%Y-%m-%d_%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    st.caption("Use esse arquivo como periodo anterior na proxima analise para o comparativo sair consistente.")

    if camp_agg_prev is not None and isinstance(camp_agg_prev, pd.DataFrame) and not camp_agg_prev.empty:
        st.divider()
        st.subheader("Comparativo vs periodo anterior")

        try:
            invest_prev = _sum_col(camp_agg_prev, "Investimento")
            rec_prev = _sum_col(camp_agg_prev, "Receita")
            roas_prev = _safe_div(rec_prev, invest_prev)
            acos_prev = _safe_div(invest_prev, rec_prev)

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Investimento", _money(inv_ads), delta=_money(inv_ads - invest_prev))
            c2.metric("Receita Ads", _money(rev_ads), delta=_money(rev_ads - rec_prev))
            c3.metric("ROAS", f"{roas:.2f}", delta=f"{(roas - roas_prev):+.2f}")
            c4.metric("ACOS", _pct(acos_ref), delta=f"{(acos_ref - acos_prev) * 100:+.2f}%".replace(".", ","))
        except Exception:
            st.warning("Nao consegui montar o comparativo de KPIs (verifique o snapshot).")

        # Comparativo por campanha (opcional)
        if camp_strat_prev is not None and isinstance(camp_strat_prev, pd.DataFrame) and not camp_strat_prev.empty:
            if "Nome" in camp_strat.columns and "Nome" in camp_strat_prev.columns:
                now_cols = [c for c in ["Nome", "Receita", "Investimento", "ROAS_Real", "Quadrante", "Acao_Recomendada"] if c in camp_strat.columns]
                prev_cols = [c for c in ["Nome", "Receita", "Investimento", "ROAS_Real"] if c in camp_strat_prev.columns]

                now = camp_strat[now_cols].copy()
                prev = camp_strat_prev[prev_cols].copy()

                for c0 in ["Receita", "Investimento", "ROAS_Real"]:
                    if c0 in now.columns:
                        now[c0] = pd.to_numeric(now[c0], errors="coerce").fillna(0)
                    if c0 in prev.columns:
                        prev[c0] = pd.to_numeric(prev[c0], errors="coerce").fillna(0)

                m = now.merge(prev, on="Nome", how="left", suffixes=("_now", "_prev")).fillna(0)

                if "Receita_now" in m.columns and "Receita_prev" in m.columns:
                    m["Delta_Receita"] = m["Receita_now"] - m["Receita_prev"]
                if "ROAS_Real_now" in m.columns and "ROAS_Real_prev" in m.columns:
                    m["Delta_ROAS"] = m["ROAS_Real_now"] - m["ROAS_Real_prev"]

                st.subheader("Campanhas que mais mudaram")
                if "Delta_Receita" in m.columns:
                    top_up = m.sort_values("Delta_Receita", ascending=False).head(10)
                    top_down = m.sort_values("Delta_Receita", ascending=True).head(10)

                    c1, c2 = st.columns(2)
                    with c1:
                        st.write("Top 10 maior alta de receita")
                        st.dataframe(safe_for_streamlit(top_up), use_container_width=True)
                    with c2:
                        st.write("Top 10 maior queda de receita")
                        st.dataframe(safe_for_streamlit(top_down), use_container_width=True)

with tab2:
    st.subheader("Gerar relatorio final (Excel)")
    st.caption("Exporta tabelas do periodo atual. Snapshot é separado e serve para historico.")

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
