import streamlit as st
from datetime import datetime
import ml_report as ml

st.set_page_config(page_title="ML Ads - Dashboard & Relatorio", layout="wide")
st.title("Mercado Livre Ads - Dashboard e Relatorio Automatico (Estrategico)")

modo = st.radio(
    "Selecione o tipo de relatorio de campanhas que voce exportou:",
    ["CONSOLIDADO (decisao)", "DIARIO (monitoramento)"],
    horizontal=True
)
modo_key = "consolidado" if "CONSOLIDADO" in modo else "diario"

with st.expander("Regras (ajustaveis)"):
    c1, c2, c3, c4 = st.columns(4)
    enter_visitas_min = c1.number_input("Entrar em Ads: visitas min", value=40, step=5)
    enter_conv_pct = c2.number_input("Entrar em Ads: conv % min", value=2.0, step=0.5)
    pause_invest_min = c3.number_input("Pausar: investimento min (R$)", value=30.0, step=10.0)
    pause_cvr_pct = c4.number_input("Pausar: conv % max", value=0.6, step=0.1)

st.markdown("### Upload dos relatorios (mesmo periodo)")
campanhas_file = st.file_uploader("Relatorio de Campanhas (Excel)", type=["xlsx", "xls"])
patrocinados_file = st.file_uploader("Relatorio de Anuncios Patrocinados (Excel)", type=["xlsx", "xls"])
organico_file = st.file_uploader("Relatorio de Publicacoes/Organico (Excel)", type=["xlsx", "xls"])

if not campanhas_file or not patrocinados_file or not organico_file:
    st.info("Suba os 3 arquivos para gerar a analise.")
    st.stop()

with st.spinner("Lendo arquivos..."):
    org = ml.load_organico(organico_file)
    pat = ml.load_patrocinados(patrocinados_file)
    camp = ml.load_campanhas_consolidado(campanhas_file) if modo_key == "consolidado" else ml.load_campanhas_diario(campanhas_file)
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
plan7 = ml.build_7_day_plan(camp_strat)

# Rankings
r_camp = ml.rank_campanhas(camp_strat, top_n=10)
r_ads = ml.rank_anuncios_patrocinados(pat, top_n=10)

tab1, tab2 = st.tabs(["Dashboard", "Gerar Excel"])

with tab1:
    st.subheader("Diagnostico Executivo")
    st.write(f"ROAS da conta: **{diagnosis['ROAS']:.2f}** | ACOS real: **{diagnosis['ACOS_real']:.2f}**")
    st.write(f"**Veredito:** {diagnosis['Veredito']}")

    t = diagnosis.get("Tendencias", {})
    if t and (t.get("cpc_proxy_up") is not None):
        st.caption(
            f"Tendencia (proxy): CPC {'subiu' if t['cpc_proxy_up'] else 'caiu/estavel'} | "
            f"Ticket medio {'caiu' if t['ticket_down'] else 'subiu/estavel'} | "
            f"Custo marginal {'piorou' if t['cm_piorou'] else 'melhorou/estavel'}"
        )

    st.divider()

    st.subheader("Top 10 campanhas por Receita (fixo)")
    bar = camp_agg.copy()
    for col in ["Receita", "Investimento", "Vendas", "ROAS", "CVR"]:
        if col in bar.columns:
            bar[col] = bar[col].astype(float)
    bar = bar.sort_values("Receita", ascending=False).head(10).set_index("Nome")
    st.bar_chart(bar[["Receita"]])

    st.divider()

    st.subheader("Matriz de Oportunidade (Destaques)")
    cA, cB = st.columns(2)
    with cA:
        st.write("Locomotivas (CPI 80% + perda por classificacao)")
        st.dataframe(high["Locomotivas"], use_container_width=True)
    with cB:
        st.write("Minas Limitadas (ROAS alto + perda por orcamento)")
        st.dataframe(high["Minas"], use_container_width=True)

    st.divider()

    st.subheader("Plano de Acao - 7 dias")
    st.dataframe(plan7, use_container_width=True)

    st.divider()

    st.subheader("Painel de Controle Geral (todas as campanhas)")
    st.dataframe(panel, use_container_width=True)

    st.divider()

    st.subheader("Rankings")

    st.markdown("### Top 10 melhores campanhas")
    cols_best = [c for c in ["Nome","Status","Receita","Investimento","Lucro_proxy","ROAS","ROAS_calc","ACOS_calc","ACOS Objetivo","Perdidas_Orc","Perdidas_Class","AÇÃO"] if c in r_camp["best"].columns]
    st.dataframe(r_camp["best"][cols_best], use_container_width=True)

    st.markdown("### Top 10 piores campanhas, acao imediata")
    cols_worst = [c for c in ["Nome","Status","Receita","Investimento","Lucro_proxy","ROAS","ROAS_calc","ACOS_calc","ACOS Objetivo","Perdidas_Orc","Perdidas_Class","AÇÃO"] if c in r_camp["worst"].columns]
    st.dataframe(r_camp["worst"][cols_worst], use_container_width=True)

    st.markdown("### Top 10 melhores anuncios patrocinados")
    cols_ads = [c for c in ["Código do anúncio","ID","Titulo do anúncio","Título do anúncio","Impressões","Cliques","Receita\n(Moeda local)","Investimento\n(Moeda local)","Lucro_proxy","ROAS_calc","ACOS_calc"] if c in r_ads["best"].columns]
    st.dataframe(r_ads["best"][cols_ads], use_container_width=True)

    st.markdown("### Top 10 piores anuncios patrocinados, acao imediata")
    cols_ads2 = [c for c in ["Código do anúncio","ID","Titulo do anúncio","Título do anúncio","Impressões","Cliques","Receita\n(Moeda local)","Investimento\n(Moeda local)","Lucro_proxy","ROAS_calc","ACOS_calc"] if c in r_ads["worst"].columns]
    st.dataframe(r_ads["worst"][cols_ads2], use_container_width=True)

    if r_ads.get("best_by_campaign") is not None:
        st.markdown("### Top anuncios por campanha")
        st.caption(f"Coluna de campanha detectada: {r_ads.get('campaign_col')}")
        ccol = r_ads.get("campaign_col")
        cols_bc = [c for c in [ccol,"Código do anúncio","Receita\n(Moeda local)","Investimento\n(Moeda local)","Lucro_proxy","ROAS_calc"] if c in r_ads["best_by_campaign"].columns]
        st.dataframe(r_ads["best_by_campaign"][cols_bc], use_container_width=True)
    else:
        st.info("Seu relatorio de anuncios patrocinados nao trouxe coluna de campanha. Mantive ranking geral de anuncios.")

    st.divider()

    cC, cD = st.columns(2)
    with cC:
        st.subheader("Campanhas para PAUSAR/REVISAR")
        st.dataframe(pause, use_container_width=True)
    with cD:
        st.subheader("Anuncios para ENTRAR em Ads (organico forte)")
        st.dataframe(enter, use_container_width=True)

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
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        st.success("OK")
