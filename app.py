import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

import ml_report as ml

st.set_page_config(page_title="ML Ads - Relatorio Estrategico", layout="wide")
st.title("Mercado Livre Ads - Relatorio Estrategico")

def safe_for_streamlit(df):
    if df is None:
        return pd.DataFrame()
    if not isinstance(df, pd.DataFrame):
        try:
            df = pd.DataFrame(df)
        except Exception:
            return pd.DataFrame()

    out = df.copy()
    out.columns = [str(c) for c in out.columns]
    out = out.loc[:, ~out.columns.duplicated()].copy()
    out = out.reset_index(drop=True)
    out = out.replace([np.inf, -np.inf], np.nan)

    for c in out.columns:
        s = out[c]
        if pd.api.types.is_datetime64_any_dtype(s):
            out[c] = s.dt.strftime("%Y-%m-%d")
            continue

        def _is_complex(x):
            return isinstance(x, (list, dict, tuple, set))

        if s.map(lambda x: _is_complex(x) if pd.notna(x) else False).any():
            out[c] = s.astype(str)
            continue

        if s.dtype == "object":
            num = pd.to_numeric(s, errors="coerce")
            if num.notna().mean() >= 0.7:
                out[c] = num
            else:
                out[c] = s.astype(str)

    return out


with st.expander("Config (opcional)"):
    plano_dias = st.selectbox("Plano de acao em quantos dias?", options=[7, 15], index=1)
    enter_visitas_min = st.number_input("Entrar em Ads: visitas min", value=40, step=5)
    enter_conv_pct = st.number_input("Entrar em Ads: conversao % min", value=2.0, step=0.5)
    pause_invest_min = st.number_input("Pausar: investimento min (R$)", value=30.0, step=10.0)
    pause_cvr_pct = st.number_input("Pausar: conversao % max", value=0.6, step=0.1)

st.markdown("### Upload dos relatorios (mesmo periodo)")

campanhas_file = st.file_uploader("Relatorio de Campanhas (Excel)", type=["xlsx", "xls"])
patrocinados_file = st.file_uploader("Relatorio de Anuncios Patrocinados (Excel)", type=["xlsx", "xls"])
organico_file = st.file_uploader("Relatorio de Publicacoes/Organico (Excel) (opcional)", type=["xlsx", "xls"])

st.markdown("### Historico comparativo (opcional)")
st.caption("Recomendado: use o snapshot padrao do app como periodo anterior.")

prev_snapshot_file = st.file_uploader("Snapshot do periodo anterior (padrão do app)", type=["xlsx"], key="prev_snapshot")
prev_campanhas_file = st.file_uploader("Campanhas (periodo anterior, Excel do ML) (opcional)", type=["xlsx", "xls"], key="prev_camp_fallback")

if campanhas_file is None or patrocinados_file is None:
    st.info("Suba Campanhas e Anuncios Patrocinados para gerar a analise.")
    st.stop()

with st.spinner("Lendo arquivos..."):
    camp = ml.load_campanhas_consolidado(campanhas_file)
    pat = ml.load_patrocinados(patrocinados_file)

    if organico_file is not None:
        org = ml.load_organico(organico_file)
    else:
        org = pd.DataFrame()

with st.spinner("Processando..."):
    camp_agg = ml.build_campaign_agg(camp, modo="consolidado")

    kpis, pause, enter, scale, acos, camp_strat = ml.build_tables(
        org, camp_agg, pat,
        enter_visitas_min=int(enter_visitas_min),
        enter_conv_min=float(enter_conv_pct) / 100.0,
        pause_invest_min=float(pause_invest_min),
        pause_cvr_max=float(pause_cvr_pct) / 100.0,
    )

    diagnosis = ml.build_executive_diagnosis(camp_strat, daily=None)
    panel = ml.build_control_panel(camp_strat)
    high = ml.build_opportunity_highlights(camp_strat)

    plan_df = ml.build_plan(camp_strat, days=int(plano_dias))

    r_camp = ml.rank_campanhas(camp_strat, top_n=10)
    r_ads = ml.rank_anuncios_patrocinados(pat, top_n=10)

# Snapshot do período atual
snapshot_bytes = ml.generate_snapshot_excel(
    camp_agg=camp_agg,
    camp_strat=camp_strat,
    period_label="Periodo atual",
    start_date="",
    end_date=""
)

# Histórico comparativo
comp_summary = None
comp_campaigns = None
trend_alerts = None
prev_meta = None

if prev_snapshot_file is not None:
    with st.spinner("Lendo snapshot do periodo anterior..."):
        prev_camp_agg, prev_camp_strat, prev_meta = ml.load_snapshot_excel(prev_snapshot_file)

    comp_summary = ml.compare_periods(camp_agg, prev_camp_agg)
    comp_campaigns = ml.compare_campaigns(camp_strat, prev_camp_strat)
    trend_alerts = ml.build_trend_alerts(comp_summary)

elif prev_campanhas_file is not None:
    with st.spinner("Lendo periodo anterior (Excel do ML)..."):
        prev_camp = ml.load_campanhas_consolidado(prev_campanhas_file)
        prev_camp_agg = ml.build_campaign_agg(prev_camp, modo="consolidado")
        prev_camp_strat = ml.add_strategy_fields(prev_camp_agg)

    comp_summary = ml.compare_periods(camp_agg, prev_camp_agg)
    comp_campaigns = ml.compare_campaigns(camp_strat, prev_camp_strat)
    trend_alerts = ml.build_trend_alerts(comp_summary)

tab1, tab2 = st.tabs(["Dashboard", "Baixar Excel"])

with tab1:
    st.subheader("Diagnostico Executivo")
    st.write(f"ROAS da conta: **{diagnosis['ROAS']:.2f}** | ACOS real: **{diagnosis['ACOS_real']:.2f}**")
    st.write(f"Veredito: **{diagnosis['Veredito']}**")

    st.divider()

    st.subheader("Matriz de Oportunidade (Destaques)")
    c1, c2 = st.columns(2)
    with c1:
        st.write("Locomotivas (CPI80% + perda por classificacao)")
        st.dataframe(safe_for_streamlit(high.get("Locomotivas")), use_container_width=True)
    with c2:
        st.write("Minas Limitadas (ROAS alto + perda por orcamento)")
        st.dataframe(safe_for_streamlit(high.get("Minas")), use_container_width=True)

    st.divider()

    st.subheader(f"Plano de Acao - {plano_dias} dias")
    st.dataframe(safe_for_streamlit(plan_df), use_container_width=True)

    st.divider()

    st.subheader("Painel de Controle Geral")
    st.dataframe(safe_for_streamlit(panel), use_container_width=True)

    st.divider()

    st.subheader("Top 10 melhores campanhas")
    st.dataframe(safe_for_streamlit(r_camp["best"]), use_container_width=True)

    st.subheader("Top 10 piores campanhas")
    st.dataframe(safe_for_streamlit(r_camp["worst"]), use_container_width=True)

    st.subheader("Top 10 melhores anuncios patrocinados")
    st.dataframe(safe_for_streamlit(r_ads["best"]), use_container_width=True)

    st.subheader("Top 10 piores anuncios patrocinados")
    st.dataframe(safe_for_streamlit(r_ads["worst"]), use_container_width=True)

    st.divider()

    c3, c4 = st.columns(2)
    with c3:
        st.subheader("Campanhas para PAUSAR/REVISAR")
        st.dataframe(safe_for_streamlit(pause), use_container_width=True)
    with c4:
        st.subheader("Anuncios para ENTRAR em Ads (organico forte)")
        if org.empty:
            st.info("Relatorio organico nao enviado. Esta parte fica desativada.")
        else:
            st.dataframe(safe_for_streamlit(enter), use_container_width=True)

    st.divider()
    st.subheader("Snapshot do periodo")
    st.caption("Baixe e use como periodo anterior na proxima analise para garantir leitura 100% consistente.")
    st.download_button(
        "Baixar snapshot padrao (Excel)",
        data=snapshot_bytes,
        file_name="snapshot_periodo_atual.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.divider()
    st.subheader("Historico comparativo")

    if comp_summary is None:
        st.info("Para ver o comparativo, envie um snapshot do periodo anterior ou o Excel de Campanhas do periodo anterior.")
    else:
        if trend_alerts:
            st.write("Alertas de tendencia")
            for a in trend_alerts:
                st.warning(a)

        if prev_meta is not None and not prev_meta.empty:
            try:
                meta_row = prev_meta.iloc[0].to_dict()
                st.caption(f"Snapshot anterior: {meta_row.get('period_label','')} | Gerado em: {meta_row.get('generated_at','')}")
            except Exception:
                pass

        st.write("Resumo: periodo atual vs anterior")
        st.dataframe(safe_for_streamlit(comp_summary), use_container_width=True)

        st.write("Campanhas com maior ganho de receita")
        if "Receita Δ%" in comp_campaigns.columns:
            top_up = comp_campaigns.sort_values("Receita Δ%", ascending=False).head(15)
            cols = [c for c in ["Nome", "Receita", "Receita (ant)", "Receita Δ%", "ROAS_calc", "ROAS_calc (ant)", "ROAS Δ", "Quadrante", "AÇÃO"] if c in top_up.columns]
            st.dataframe(safe_for_streamlit(top_up[cols]), use_container_width=True)

        st.write("Campanhas com maior queda de ROAS")
        if "ROAS Δ" in comp_campaigns.columns:
            top_down = comp_campaigns.sort_values("ROAS Δ", ascending=True).head(15)
            cols = [c for c in ["Nome", "ROAS_calc", "ROAS_calc (ant)", "ROAS Δ", "Investimento", "Investimento (ant)", "Investimento Δ%", "Quadrante", "AÇÃO"] if c in top_down.columns]
            st.dataframe(safe_for_streamlit(top_down[cols]), use_container_width=True)

with tab2:
    st.subheader("Gerar relatorio final (Excel)")
    if st.button("Gerar e baixar Excel"):
        with st.spinner("Gerando Excel..."):
            bytes_xlsx = ml.gerar_excel(
                kpis, camp_agg, pause, enter, scale, acos, camp_strat,
                daily=None,
                plan_df=plan_df
            )

        nome = f"Relatorio_ML_ADs_{datetime.now().strftime('%Y-%m-%d_%H%M')}.xlsx"
        st.download_button(
            "Baixar Excel",
            data=bytes_xlsx,
            file_name=nome,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        st.success("OK")
