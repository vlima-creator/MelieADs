import streamlit as st
import pandas as pd
import numpy as np

import ml_report as ml


st.set_page_config(page_title="Mercado Livre Ads - Relatório Estratégico", layout="wide")

st.title("Mercado Livre Ads, Relatório Estratégico")
st.caption("Suba Campanhas + Anúncios patrocinados. Publicações (orgânico) é opcional e habilita TACOS.")


def _money(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "R$ 0,00"
    try:
        return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def _pct(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "0,00%"
    try:
        return f"{float(v) * 100:.2f}%".replace(".", ",")
    except Exception:
        return "0,00%"


def _float(v, default=0.0):
    try:
        if v is None:
            return default
        if isinstance(v, float) and np.isnan(v):
            return default
        return float(v)
    except Exception:
        return default


with st.sidebar:
    st.subheader("Config")
    periodo_label = st.text_input("Rótulo do período", value="Últimos 15 dias")

    modo = st.selectbox(
        "Tipo de arquivo de Campanhas",
        options=["auto", "consolidado", "diario"],
        index=0,
        help="Auto tenta detectar. Consolidado e Diário forçam o leitor."
    )

    top_n = st.slider("Top N (rankings)", min_value=5, max_value=30, value=10, step=1)

st.divider()

camp_file = st.file_uploader("Relatório de Campanhas (Excel ou CSV)", type=["xlsx", "xls", "csv"], key="camp")
pat_file = st.file_uploader("Relatório de Anúncios patrocinados (Excel ou CSV)", type=["xlsx", "xls", "csv"], key="pat")
org_file = st.file_uploader("Relatório de Publicações, Orgânico (opcional)", type=["xlsx", "xls"], key="org")

st.divider()

if not camp_file or not pat_file:
    st.info("Suba Campanhas e Anúncios patrocinados para gerar o relatório.")
    st.stop()

try:
    if modo == "diario":
        camp_raw = ml.load_campanhas_diario(camp_file)
    elif modo == "consolidado":
        camp_raw = ml.load_campanhas_consolidado(camp_file)
    else:
        # auto: tenta consolidado, se falhar cai para diario
        try:
            camp_raw = ml.load_campanhas_consolidado(camp_file)
        except Exception:
            camp_raw = ml.load_campanhas_diario(camp_file)

    pat = ml.load_patrocinados(pat_file)

    org = None
    if org_file is not None:
        org = ml.load_organico(org_file)

    camp_agg = ml.build_campaign_agg(camp_raw, modo_key=modo)

except Exception as e:
    st.error("Falha ao ler os arquivos. O ML pode ter mudado a estrutura.")
    st.exception(e)
    st.stop()

kpis = ml.build_kpis(camp_agg, pat, org)

st.subheader("KPIs")
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Investimento", _money(kpis.get("Investimento Ads (R$)", 0)))
c2.metric("Receita Ads", _money(kpis.get("Receita Ads (R$)", 0)))
c3.metric("Vendas Ads", f"{int(_float(kpis.get('Vendas Ads (qtd)', 0))):,}".replace(",", "."))
c4.metric("ROAS", f"{_float(kpis.get('ROAS', 0)):.2f}")
c5.metric("Campanhas únicas", str(kpis.get("Campanhas únicas", 0)))
c6.metric("IDs patrocinados", str(kpis.get("IDs patrocinados", 0)))

if kpis.get("Faturamento total estimado (R$)") is not None:
    st.divider()
    c7, c8, c9 = st.columns(3)
    c7.metric("Faturamento total estimado", _money(kpis.get("Faturamento total estimado (R$)", 0)))
    c8.metric("TACOS (conta)", _pct(kpis.get("TACOS (conta)", 0)))
    c9.metric("ACOS (referência)", _pct(kpis.get("ACOS", 0)))
    st.caption("TACOS usa faturamento total (orgânico + pago). ACOS usa apenas receita de Ads.")

st.divider()

st.subheader("Painel de Controle Geral, Campanhas (normalizado)")
st.dataframe(camp_agg, use_container_width=True)

st.divider()

if org is not None and len(org) > 0:
    st.subheader(f"Rankings TACOS (Top {top_n})")

    best, worst = ml.build_tacos_ranking(pat, org, top_n=top_n)

    if len(best) == 0:
        st.warning("Não consegui montar o ranking TACOS. Confere se o orgânico tem ID e Vendas brutas.")
    else:
        st.markdown(f"### Top {top_n} melhores produtos por TACOS (menor TACOS)")
        st.dataframe(best, use_container_width=True)

        st.markdown(f"### Top {top_n} piores produtos por TACOS (maior TACOS)")
        st.dataframe(worst, use_container_width=True)

st.divider()

st.subheader("Histórico comparativo (opcional)")
st.caption("Baixe o snapshot do app e use ele como período anterior na próxima análise.")

snapshot_bytes = ml.export_snapshot_excel(
    camp_agg=camp_agg,
    pat=pat,
    org=org,
    kpis=kpis,
    periodo_label=periodo_label
)

st.download_button(
    "Baixar snapshot padrão do app (Excel)",
    data=snapshot_bytes,
    file_name=f"snapshot_mlads_{periodo_label.replace(' ', '_').lower()}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

snap_prev = st.file_uploader("Snapshot do período anterior (padrão do app)", type=["xlsx"], key="snap_prev")

if snap_prev is not None:
    try:
        prev_camp, prev_pat, prev_org, prev_kpis = ml.read_snapshot_excel(snap_prev)

        st.markdown("### Comparativo KPIs, atual vs anterior")

        atual_inv = _float(kpis.get("Investimento Ads (R$)", 0))
        atual_rec = _float(kpis.get("Receita Ads (R$)", 0))
        atual_roas = _float(kpis.get("ROAS", 0))

        prev_row = prev_kpis.iloc[0].to_dict() if isinstance(prev_kpis, pd.DataFrame) and len(prev_kpis) else {}
        prev_inv = _float(prev_row.get("Investimento Ads (R$)", 0))
        prev_rec = _float(prev_row.get("Receita Ads (R$)", 0))
        prev_roas = _float(prev_row.get("ROAS", 0))

        cc1, cc2, cc3 = st.columns(3)
        cc1.metric("Investimento", _money(atual_inv), delta=_money(atual_inv - prev_inv))
        cc2.metric("Receita Ads", _money(atual_rec), delta=_money(atual_rec - prev_rec))
        cc3.metric("ROAS", f"{atual_roas:.2f}", delta=f"{(atual_roas - prev_roas):.2f}")

    except Exception as e:
        st.error("Falha ao ler o snapshot anterior.")
        st.exception(e)
