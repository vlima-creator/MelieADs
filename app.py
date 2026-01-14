import streamlit as st

st.set_page_config(page_title="ML Ads - Relatório Estratégico", layout="wide")

st.title("Mercado Livre Ads, Relatório Estratégico")
st.caption("Upload dos arquivos, clique em Gerar, receba decisões prontas.")

with st.expander("Checklist rápido", expanded=True):
    st.write("1) Suba o Relatório de Campanhas do período.")
    st.write("2) Suba o Relatório de Anúncios Patrocinados do mesmo período.")
    st.write("3) Clique em Gerar relatório.")
    st.write("Dica: se Excel estiver pesado, exporte como CSV e suba CSV.")

period_label = st.text_input("Rótulo do período", value="Últimos 15 dias")

camp_file = st.file_uploader(
    "Relatório de Campanhas (CSV ou Excel)",
    type=["csv", "xlsx", "xls"],
    accept_multiple_files=False
)

ads_file = st.file_uploader(
    "Relatório de Anúncios Patrocinados (CSV ou Excel)",
    type=["csv", "xlsx", "xls"],
    accept_multiple_files=False
)

btn = st.button("Gerar relatório", type="primary", use_container_width=True)

# -------------------------
# Só roda análise ao clicar
# -------------------------
if btn:
    if camp_file is None:
        st.error("Suba o Relatório de Campanhas primeiro.")
        st.stop()

    # Imports pesados só aqui, para o app abrir rápido
    import pandas as pd

    def read_any(file):
        name = file.name.lower()
        if name.endswith(".csv"):
            return pd.read_csv(file)
        return pd.read_excel(file, engine="openpyxl")

    def find_col(df, candidates):
        cols = {c.lower(): c for c in df.columns}
        for cand in candidates:
            if cand.lower() in cols:
                return cols[cand.lower()]
        for c in df.columns:
            cl = c.lower()
            for cand in candidates:
                if cand.lower() in cl:
                    return c
        return None

    def to_number_series(s: pd.Series) -> pd.Series:
        if pd.api.types.is_numeric_dtype(s):
            return s.astype(float)

        x = s.astype(str).str.strip()
        is_percent = x.str.contains("%", na=False)

        x = (
            x.str.replace("R$", "", regex=False)
             .str.replace("$", "", regex=False)
             .str.replace("%", "", regex=False)
             .str.replace("\u00a0", " ", regex=False)
             .str.replace(" ", "", regex=False)
             .str.replace(".", "", regex=False)    # milhar pt-br
             .str.replace(",", ".", regex=False)   # decimal pt-br
        )
        v = pd.to_numeric(x, errors="coerce")
        v = v.where(~is_percent, v / 100.0)
        return v.astype(float)

    def safe_div(a, b):
        b = b.replace(0, pd.NA)
        return a / b

    def fmt_money(v):
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return "-"
        return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def fmt_pct(v):
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return "-"
        return f"{float(v)*100:.1f}%".replace(".", ",")

    # -------------------------
    # Leitura
    # -------------------------
    with st.spinner("Lendo campanhas..."):
        df_c = read_any(camp_file)
        df_c.columns = [str(c).strip() for c in df_c.columns]

    # Colunas mínimas
    col_name = find_col(df_c, ["Nome da Campanha", "Campanha", "Campaign", "Nome"])
    col_spend = find_col(df_c, ["Investimento", "Gasto", "Custo", "Spend"])
    col_revenue = find_col(df_c, ["Receita", "Vendas", "Sales", "Faturamento"])

    col_budget = find_col(df_c, ["Orçamento", "Orçamento diário", "Budget", "Orçamento médio diário"])
    col_acos_target = find_col(df_c, ["ACOS Objetivo", "ACOS alvo", "ACOS objetivo"])
    col_loss_budget = find_col(df_c, ["Perda por Orçamento", "% Perda Orçamento", "Loss budget"])
    col_loss_rank = find_col(df_c, ["Perda por Classificação", "% Perda Classificação", "Perda por rank", "Loss rank"])

    if col_name is None or col_spend is None or col_revenue is None:
        st.error("Não achei colunas mínimas em Campanhas. Preciso de: Nome da Campanha, Investimento/Gasto e Receita/Vendas.")
        st.stop()

    keep = [c for c in [col_name, col_spend, col_revenue, col_budget, col_acos_target, col_loss_budget, col_loss_rank] if c]
    df = df_c[keep].copy()

    for c in [col_spend, col_revenue, col_budget, col_acos_target, col_loss_budget, col_loss_rank]:
        if c and c in df.columns:
            df[c] = to_number_series(df[c])

    df["Campanha"] = df[col_name].astype(str)
    df["Investimento"] = df[col_spend]
    df["Receita"] = df[col_revenue]
    df["ROAS"] = safe_div(df["Receita"], df["Investimento"])
    df["ACOS_real"] = safe_div(df["Investimento"], df["Receita"])

    df["Orçamento_atual"] = df[col_budget] if col_budget else pd.NA
    df["ACOS_objetivo"] = df[col_acos_target] if col_acos_target else pd.NA
    df["Perda_orc"] = df[col_loss_budget] if col_loss_budget else pd.NA
    df["Perda_rank"] = df[col_loss_rank] if col_loss_rank else pd.NA

    # Pareto
    df = df.sort_values("Receita", ascending=False).reset_index(drop=True)
    total_rev = df["Receita"].sum(skipna=True)
    total_inv = df["Investimento"].sum(skipna=True)
    df["rev_share"] = df["Receita"] / total_rev if total_rev else pd.NA
    df["rev_cum"] = df["rev_share"].cumsum()
    df["Prioridade_Pareto"] = df["rev_cum"] <= 0.80

    # Quadrantes
    med = df["Receita"].median(skipna=True)
    receita_relevante = (df["Receita"] >= med) | (df["Prioridade_Pareto"] == True)

    escala_orc = (df["ROAS"] > 7) & (df["Perda_orc"] > 0.40)
    competitividade = receita_relevante & (df["Perda_rank"] > 0.50)
    hemorragia = (df["ROAS"] < 3) | ((df["ACOS_real"] > (df["ACOS_objetivo"] * 1.35)) & (~pd.isna(df["ACOS_objetivo"])))

    df["Quadrante"] = "ESTÁVEL"
    df.loc[hemorragia, "Quadrante"] = "HEMORRAGIA"
    df.loc[competitividade, "Quadrante"] = "COMPETITIVIDADE"
    df.loc[escala_orc, "Quadrante"] = "ESCALA DE ORÇAMENTO"

    def action(q):
        if q == "ESCALA DE ORÇAMENTO":
            return "🟢 Aumentar Orçamento"
        if q == "COMPETITIVIDADE":
            return "🟡 Subir ACOS Alvo"
        if q == "HEMORRAGIA":
            return "🔴 Revisar/Pausar"
        return "🔵 Manter"

    df["AÇÃO RECOMENDADA"] = df["Quadrante"].map(action)

    roas_conta = (total_rev / total_inv) if total_inv else float("nan")
    acos_conta = (total_inv / total_rev) if total_rev else float("nan")

    # -------------------------
    # Relatório (formato fixo)
    # -------------------------
    st.markdown("## Relatório Estratégico de Performance")
    st.caption(period_label)

    st.markdown("### 1. Diagnóstico Executivo")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Receita (Ads)", fmt_money(total_rev))
    c2.metric("Investimento", fmt_money(total_inv))
    c3.metric("ROAS da conta", "-" if pd.isna(roas_conta) else f"{roas_conta:.2f}")
    c4.metric("ACOS da conta", fmt_pct(acos_conta))

    if not pd.isna(roas_conta) and roas_conta >= 7:
        veredito = "Estamos deixando dinheiro na mesa. Escale minas e destrave rank, cortando sangrias."
    elif not pd.isna(roas_conta) and roas_conta < 3:
        veredito = "Precisamos estancar sangria. Corte detratores e ajuste funil antes de escalar."
    else:
        veredito = "Conta intermediária. Escale só onde o gargalo é verba ou rank. Corte hemorragias."

    st.write(f"- Veredito: {veredito}")

    st.markdown("### 2. Análise de Oportunidades (Matriz CPI)")
    game = df[df["Prioridade_Pareto"]].head(10)

    st.markdown("**As Locomotivas (Faturamento alto + problema de rank)**")
    st.dataframe(game[game["Quadrante"] == "COMPETITIVIDADE"][["Campanha","Receita","Investimento","ROAS","Perda_rank","AÇÃO RECOMENDADA"]], use_container_width=True)

    st.markdown("**As Minas Limitadas (ROAS alto + falta de verba)**")
    st.dataframe(game[game["Quadrante"] == "ESCALA DE ORÇAMENTO"][["Campanha","Receita","Investimento","ROAS","Perda_orc","AÇÃO RECOMENDADA"]], use_container_width=True)

    st.markdown("**Hemorragias (detratoras)**")
    st.dataframe(game[game["Quadrante"] == "HEMORRAGIA"][["Campanha","Receita","Investimento","ROAS","ACOS_real","AÇÃO RECOMENDADA"]], use_container_width=True)

    st.markdown("### 3. Plano de Ação Tático (Próximos 7 Dias)")
    minas = game[game["Quadrante"] == "ESCALA DE ORÇAMENTO"].head(5)
    loco = game[game["Quadrante"] == "COMPETITIVIDADE"].head(5)
    hemo = game[game["Quadrante"] == "HEMORRAGIA"].head(5)

    st.markdown("**Dia 1 (Destravar):**")
    if len(minas):
        for n in minas["Campanha"].tolist():
            st.write(f"- 🟢 Aumente orçamento: {n}")
    else:
        st.write("- 🟢 Aumente orçamento nas campanhas com ROAS alto e sinais de teto de verba.")

    st.markdown("**Dia 2 (Competir):**")
    if len(loco):
        for n in loco["Campanha"].tolist():
            st.write(f"- 🟡 Suba ACOS objetivo: {n}")
    else:
        st.write("- 🟡 Suba ACOS objetivo nas campanhas com receita relevante que estão perdendo rank.")

    st.markdown("**Dia 3 (Estancar):**")
    if len(hemo):
        for n in hemo["Campanha"].tolist():
            st.write(f"- 🔴 Reduza agressividade ou pause: {n}")
    else:
        st.write("- 🔴 Corte campanhas com ROAS < 3 sem tese clara.")

    st.markdown("**Dia 5 (Monitorar):**")
    st.write("- Monitore ROAS pós mudanças e se receita cresce mais rápido que investimento.")

    st.markdown("### 4. 📋 Painel de Controle Geral")
    painel = df[["Campanha","Orçamento_atual","ACOS_objetivo","ROAS","Perda_orc","Perda_rank","AÇÃO RECOMENDADA"]].copy()
    painel = painel.rename(columns={
        "Campanha":"Nome da Campanha",
        "Orçamento_atual":"Orçamento Atual",
        "ACOS_objetivo":"ACOS Objetivo Atual",
        "ROAS":"ROAS Real (calculado)",
        "Perda_orc":"% Perda Orçamento",
        "Perda_rank":"% Perda Classificação (rank)",
    })
    st.dataframe(painel, use_container_width=True)

    # Anúncios patrocinados é opcional
    if ads_file is not None:
        with st.spinner("Lendo anúncios patrocinados..."):
            df_a = read_any(ads_file)
            df_a.columns = [str(c).strip() for c in df_a.columns]

        col_spend_a = find_col(df_a, ["Investimento", "Gasto", "Custo", "Spend"])
        col_rev_a = find_col(df_a, ["Receita", "Vendas", "Sales", "Faturamento"])
        col_roas_a = find_col(df_a, ["ROAS", "ROAS real", "ROAS Real"])
        col_title_a = find_col(df_a, ["Título do anúncio", "Titulo", "Anúncio", "Anuncio", "Item", "Publicação", "Publicacao"])
        col_mlb_a = find_col(df_a, ["MLB", "Item ID", "ID do item", "ID"])

        if col_spend_a and col_rev_a:
            keep_a = [c for c in [col_mlb_a, col_title_a, col_spend_a, col_rev_a, col_roas_a] if c]
            da = df_a[keep_a].copy()
            for c in [col_spend_a, col_rev_a, col_roas_a]:
                if c and c in da.columns:
                    da[c] = to_number_series(da[c])

            da["Investimento"] = da[col_spend_a]
            da["Receita"] = da[col_rev_a]
            da["ROAS"] = da[col_roas_a] if col_roas_a else safe_div(da["Receita"], da["Investimento"])
            da["MLB"] = da[col_mlb_a].astype(str) if col_mlb_a else "-"
            da["Anúncio"] = da[col_title_a].astype(str) if col_title_a else "Anúncio"

            estrela = (da["ROAS"] >= 7) & (da["Receita"] > 0)
            sanguessuga = (da["Investimento"] > 0) & ((da["Receita"].isna()) | (da["Receita"] == 0))
            gastao = (da["ROAS"] < 3) & (da["Receita"] > 0)

            da["Perfil"] = "NEUTRO"
            da.loc[gastao, "Perfil"] = "GASTÃO"
            da.loc[sanguessuga, "Perfil"] = "SANGUESSUGA"
            da.loc[estrela, "Perfil"] = "ESTRELA"

            st.markdown("## Corte de Sangria em Produtos e Anúncios")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown("**🔴 Sanguessugas**")
                st.dataframe(da[da["Perfil"] == "SANGUESSUGA"].sort_values("Investimento", ascending=False).head(25),
                             use_container_width=True)
            with c2:
                st.markdown("**🟡 Gastões**")
                st.dataframe(da[da["Perfil"] == "GASTÃO"].sort_values("Investimento", ascending=False).head(25),
                             use_container_width=True)
            with c3:
                st.markdown("**🟢 Estrelas**")
                st.dataframe(da[da["Perfil"] == "ESTRELA"].sort_values("Receita", ascending=False).head(25),
                             use_container_width=True)
        else:
            st.warning("Não consegui achar colunas mínimas em Anúncios Patrocinados. Vou ignorar essa parte.")
