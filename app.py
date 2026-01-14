import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

import ml_report as ml

st.set_page_config(page_title="ML Ads - Relatorio Estrategico", layout="wide")
st.title("Mercado Livre Ads - Relatorio Estrategico")

def safe_for_streamlit(df: pd.DataFrame) -> pd.DataFrame:
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

        # objetos complexos viram texto
        def _is_complex(x):
            return isinstance(x, (list, dict, tuple, set))

        if s.map(lambda x: _is_complex(x) if pd.notna(x) else False).any():
            out[c] = s.astype(str)
            continue

        # tentar converter objeto para numero se fizer sentido
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

    # Jeito 1: build_plan existe no ml_report
    plan_df = ml.build_plan(camp_strat, days=int(plano_dias))

    r_camp = ml.rank_campanhas(camp_strat, top_n=10)
    r_ads = ml.rank_anuncios_patrocinados(pat, top_n=10)

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
