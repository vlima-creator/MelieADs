import streamlit as st
import pandas as pd

st.set_page_config(page_title="ML Ads - Relatório Estratégico", layout="wide")
st.title("Mercado Livre Ads, Relatório Estratégico Automatizado")
st.caption("Suba os relatórios, clique em Gerar, receba decisões prontas.")

# =========================
# Leitura e limpeza padrão ML
# =========================

def read_any(file):
    name = file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(file, header=None)
    return pd.read_excel(file, header=None, engine="openpyxl")

def detect_header_row(df_raw: pd.DataFrame) -> int:
    best_idx = 0
    best_score = -1
    max_rows = min(len(df_raw), 40)

    for i in range(max_rows):
        row = df_raw.iloc[i].astype(str)
        filled = (row.str.strip() != "") & (row.str.lower() != "nan")
        filled_count = int(filled.sum())
        if filled_count == 0:
            continue

        numeric_like = row.str.match(r"^\s*[\d\.,%R$\-\s]+\s*$", na=False).sum()
        numeric_like = int(numeric_like)

        score = filled_count - (numeric_like * 0.6)
        if score > best_score:
            best_score = score
            best_idx = i

    return best_idx

def normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df

def clean_numeric_series(s: pd.Series) -> pd.Series:
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
         .str.replace(".", "", regex=False)
         .str.replace(",", ".", regex=False)
    )

    v = pd.to_numeric(x, errors="coerce")
    v = v.where(~is_percent, v / 100.0)
    return v.astype(float)

def ml_clean(file) -> pd.DataFrame:
    df_raw = read_any(file)
    header_idx = detect_header_row(df_raw)
    header = df_raw.iloc[header_idx].astype(str).tolist()
    df = df_raw.iloc[header_idx + 1:].copy()
    df.columns = header
    df = df.reset_index(drop=True)
    df = normalize_df(df)
    df = df.dropna(axis=1, how="all")

    # auto numeric
    for c in df.columns:
        conv = clean_numeric_series(df[c])
        if conv.notna().mean() >= 0.70:
            df[c] = conv

    return df

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

def fmt_money(v):
    if v is None or pd.isna(v):
        return "-"
    return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def fmt_pct(v):
    if v is None or pd.isna(v):
        return "-"
    return f"{float(v)*100:.1f}%".replace(".", ",")

# =========================
# Identificação do tipo
# =========================

def guess_report_type(df: pd.DataFrame) -> str:
    cols = " | ".join([c.lower() for c in df.columns])

    if ("nome da campanha" in cols or "campanha" in cols) and ("orçamento" in cols or "acos objetivo" in cols or "perda" in cols):
        return "campanhas"

    if ("mlb" in cols or "id do item" in cols or "item id" in cols) and ("investimento" in cols or "gasto" in cols) and ("roas" in cols or "acos" in cols):
        return "anuncios_patrocinados"

    if ("id do anúncio" in cols or "id do anuncio" in cols) and ("visitas únicas" in cols or "visitas unicas" in cols):
        return "publicacoes"

    return "desconhecido"

# =========================
# Análise de Campanhas
# =========================

def analyze_campaigns(df):
    col_name = find_col(df, ["Nome da Campanha", "Campanha", "Nome"])
    col_spend = find_col(df, ["Investimento", "Gasto", "Custo", "Spend"])
    col_revenue = find_col(df, ["Receita", "Vendas", "Sales", "Faturamento", "Vendas por Product Ads"])
    col_budget = find_col(df, ["Orçamento", "Orçamento diário", "Orçamento médio diário", "Budget"])
    col_acos_target = find_col(df, ["ACOS Objetivo", "ACOS alvo", "ACOS objetivo"])
    col_loss_budget = find_col(df, ["Perda por Orçamento", "% Perda Orçamento", "Loss budget"])
    col_loss_rank = find_col(df, ["Perda por Classificação", "% Perda Classificação", "Perda por rank", "Loss rank"])

    if col_name is None or col_spend is None or col_revenue is None:
        return None, "Não achei colunas mínimas em Campanhas (Nome da Campanha, Investimento, Receita)."

    out = pd.DataFrame()
    out["Campanha"] = df[col_name].astype(str)
    out["Investimento"] = df[col_spend]
    out["Receita"] = df[col_revenue]
    out["Orçamento_atual"] = df[col_budget] if col_budget else pd.NA
    out["ACOS_objetivo"] = df[col_acos_target] if col_acos_target else pd.NA
    out["Perda_orc"] = df[col_loss_budget] if col_loss_budget else pd.NA
    out["Perda_rank"] = df[col_loss_rank] if col_loss_rank else pd.NA

    out["ROAS"] = out["Receita"] / out["Investimento"].replace(0, pd.NA)
    out["ACOS_real"] = out["Investimento"] / out["Receita"].replace(0, pd.NA)

    out = out.sort_values("Receita", ascending=False).reset_index(drop=True)
    total_rev = out["Receita"].sum(skipna=True)
    total_inv = out["Investimento"].sum(skipna=True)

    out["rev_share"] = out["Receita"] / total_rev if total_rev else pd.NA
    out["rev_cum"] = out["rev_share"].cumsum()
    out["Prioridade_Pareto"] = out["rev_cum"] <= 0.80

    med = out["Receita"].median(skipna=True)
    receita_relevante = (out["Receita"] >= med) | (out["Prioridade_Pareto"] == True)

    escala_orc = (out["ROAS"] > 7) & (out["Perda_orc"] > 0.40)
    competitividade = receita_relevante & (out["Perda_rank"] > 0.50)
    hemorragia = (out["ROAS"] < 3) | ((out["ACOS_real"] > (out["ACOS_objetivo"] * 1.35)) & (~pd.isna(out["ACOS_objetivo"])))

    out["Quadrante"] = "ESTÁVEL"
    out.loc[hemorragia, "Quadrante"] = "HEMORRAGIA"
    out.loc[competitividade, "Quadrante"] = "COMPETITIVIDADE"
    out.loc[escala_orc, "Quadrante"] = "ESCALA DE ORÇAMENTO"

    action_map = {
        "ESCALA DE ORÇAMENTO": "🟢 Aumentar Orçamento",
        "COMPETITIVIDADE": "🟡 Subir ACOS Alvo",
        "HEMORRAGIA": "🔴 Revisar/Pausar",
        "ESTÁVEL": "🔵 Manter",
    }
    out["AÇÃO RECOMENDADA"] = out["Quadrante"].map(action_map)

    meta = {
        "total_receita": float(total_rev) if not pd.isna(total_rev) else 0.0,
        "total_invest": float(total_inv) if not pd.isna(total_inv) else 0.0,
        "roas_conta": (total_rev / total_inv) if total_inv else float("nan"),
        "acos_conta": (total_inv / total_rev) if total_rev else float("nan"),
        "gamechangers": out[out["Prioridade_Pareto"]].head(10),
    }
    return out, meta

# =========================
# Análise de Anúncios Patrocinados
# =========================

def analyze_sponsored_ads(df):
    col_mlb = find_col(df, ["MLB", "Item ID", "ID do item", "ID"])
    col_title = find_col(df, ["Título do anúncio", "Titulo", "Anúncio", "Anuncio", "Item"])
    col_spend = find_col(df, ["Investimento", "Gasto", "Custo", "Spend"])
    col_revenue = find_col(df, ["Receita", "Vendas", "Sales", "Faturamento"])
    col_roas = find_col(df, ["ROAS", "ROAS real", "ROAS Real"])
    col_acos = find_col(df, ["ACOS", "ACOS real", "ACOS Real"])

    if col_spend is None or col_revenue is None:
        return None, "Não achei colunas mínimas em Anúncios Patrocinados (Investimento, Receita)."

    out = pd.DataFrame()
    out["MLB"] = df[col_mlb].astype(str) if col_mlb else "-"
    out["Anúncio"] = df[col_title].astype(str) if col_title else "Anúncio"
    out["Investimento"] = df[col_spend]
    out["Receita"] = df[col_revenue]

    out["ROAS"] = df[col_roas] if col_roas else out["Receita"] / out["Investimento"].replace(0, pd.NA)
    out["ACOS_real"] = df[col_acos] if col_acos else out["Investimento"] / out["Receita"].replace(0, pd.NA)

    out.loc[out["ACOS_real"] > 2, "ACOS_real"] = out.loc[out["ACOS_real"] > 2, "ACOS_real"] / 100.0

    estrela = (out["ROAS"] >= 7) & (out["Receita"] > 0)
    sanguessuga = (out["Investimento"] > 0) & ((out["Receita"].isna()) | (out["Receita"] == 0))
    gastao = (out["ROAS"] < 3) & (out["Receita"] > 0)

    out["Perfil"] = "NEUTRO"
    out.loc[gastao, "Perfil"] = "GASTÃO"
    out.loc[sanguessuga, "Perfil"] = "SANGUESSUGA"
    out.loc[estrela, "Perfil"] = "ESTRELA"

    out = out.sort_values("Investimento", ascending=False)
    meta = {
        "top_sanguessugas": out[out["Perfil"] == "SANGUESSUGA"].head(25),
        "top_gastoes": out[out["Perfil"] == "GASTÃO"].head(25),
        "top_estrelas": out[out["Perfil"] == "ESTRELA"].sort_values("Receita", ascending=False).head(25),
    }
    return out, meta

# =========================
# Publicações (conversão por variação)
# =========================

def analyze_publicacoes(df):
    col_ad_id = find_col(df, ["ID do anúncio", "ID do anuncio"])
    col_title = find_col(df, ["Anúncio", "Anuncio"])
    col_var = find_col(df, ["Variação", "Variacao"])
    col_visits = find_col(df, ["Visitas únicas", "Visitas unicas"])
    col_sales = find_col(df, ["Quantidade de vendas", "Vendas"])
    col_gmv = find_col(df, ["Vendas brutas", "GMV"])

    if col_visits is None or col_sales is None:
        return None, "Não achei colunas mínimas em Publicações (Visitas únicas, Quantidade de vendas)."

    out = pd.DataFrame()
    out["ID anúncio"] = df[col_ad_id].astype(str) if col_ad_id else "-"
    out["Anúncio"] = df[col_title].astype(str) if col_title else "Anúncio"
    out["Variação"] = df[col_var].astype(str) if col_var else "-"
    out["Visitas"] = df[col_visits]
    out["Vendas"] = df[col_sales]
    out["GMV"] = df[col_gmv] if col_gmv else pd.NA

    out["CVR"] = out["Vendas"] / out["Visitas"].replace(0, pd.NA)
    out = out.sort_values("Visitas", ascending=False)

    # top variações ruins e boas por conversão (com mínimo de visitas)
    base = out[out["Visitas"] >= 20].copy()
    boas = base.sort_values("CVR", ascending=False).head(25)
    ruins = base.sort_values("CVR", ascending=True).head(25)

    meta = {"top_boas": boas, "top_ruins": ruins}
    return out, meta

# =========================
# UI
# =========================

period_label = st.text_input("Rótulo do período", value="Últimos 15 dias")

f1 = st.file_uploader("1) Campanhas", type=["csv", "xlsx", "xls"])
f2 = st.file_uploader("2) Anúncios patrocinados", type=["csv", "xlsx", "xls"])
f3 = st.file_uploader("3) Publicações (opcional)", type=["csv", "xlsx", "xls"])

gerar = st.button("Gerar relatório", type="primary", use_container_width=True)

if gerar:
    if not f1 or not f2:
        st.error("Preciso pelo menos de Campanhas e Anúncios patrocinados.")
        st.stop()

    with st.spinner("Limpando e lendo arquivos..."):
        df1 = ml_clean(f1)
        df2 = ml_clean(f2)
        df3 = ml_clean(f3) if f3 else None

    t1 = guess_report_type(df1)
    t2 = guess_report_type(df2)

    # garante ordem correta, mesmo se você subir invertido
    camps_df = df1 if t1 == "campanhas" else (df2 if t2 == "campanhas" else None)
    ads_df = df2 if t2 == "anuncios_patrocinados" else (df1 if t1 == "anuncios_patrocinados" else None)

    if camps_df is None or ads_df is None:
        st.error("Não consegui identificar Campanhas e Anúncios patrocinados pelos headers. Verifique se subiu os relatórios corretos.")
        st.stop()

    with st.spinner("Analisando campanhas..."):
        camp_out, camp_meta = analyze_campaigns(camps_df)
        if camp_out is None:
            st.error(camp_meta)
            st.stop()

    with st.spinner("Analisando anúncios patrocinados..."):
        ads_out, ads_meta = analyze_sponsored_ads(ads_df)
        if ads_out is None:
            st.error(ads_meta)
            st.stop()

    pub_out, pub_meta = (None, None)
    if df3 is not None:
        with st.spinner("Analisando publicações (variações e conversão)..."):
            pub_out, pub_meta = analyze_publicacoes(df3)

    # =========================
    # RELATÓRIO FINAL (FORMATO OBRIGATÓRIO)
    # =========================
    st.markdown("## Relatório Estratégico de Performance")
    st.caption(period_label)

    st.markdown("### 1. Diagnóstico Executivo")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Receita (Ads)", fmt_money(camp_meta["total_receita"]))
    c2.metric("Investimento", fmt_money(camp_meta["total_invest"]))
    c3.metric("ROAS da conta", "-" if pd.isna(camp_meta["roas_conta"]) else f"{camp_meta['roas_conta']:.2f}")
    c4.metric("ACOS da conta", fmt_pct(camp_meta["acos_conta"]))

    roas = camp_meta["roas_conta"]
    if not pd.isna(roas) and roas >= 7:
        veredito = "Estamos deixando dinheiro na mesa. Escale minas e destrave rank, cortando sangria."
    elif not pd.isna(roas) and roas < 3:
        veredito = "Precisamos estancar sangria. Corte detratores e ajuste funil antes de escalar."
    else:
        veredito = "Conta intermediária. Escale só onde o gargalo é verba ou rank. Corte hemorragias."

    st.write(f"- Veredito: {veredito}")

    st.markdown("### 2. Análise de Oportunidades (Matriz CPI)")
    game = camp_meta["gamechangers"]

    st.markdown("**As Locomotivas (Faturamento Alto + Problema de Rank)**")
    st.dataframe(game[game["Quadrante"] == "COMPETITIVIDADE"][["Campanha","Receita","Investimento","ROAS","Perda_rank","AÇÃO RECOMENDADA"]], use_container_width=True)

    st.markdown("**As Minas Limitadas (ROAS Alto + Falta de Verba)**")
    st.dataframe(game[game["Quadrante"] == "ESCALA DE ORÇAMENTO"][["Campanha","Receita","Investimento","ROAS","Perda_orc","AÇÃO RECOMENDADA"]], use_container_width=True)

    st.markdown("**Hemorragias (Detratoras)**")
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
    st.write("- Se ROAS cair forte após abrir funil, você abriu demais. Recuar e reavaliar no próximo ciclo.")

    st.markdown("### 4. 📋 Painel de Controle Geral")
    painel = camp_out[["Campanha","Orçamento_atual","ACOS_objetivo","ROAS","Perda_orc","Perda_rank","AÇÃO RECOMENDADA"]].copy()
    painel = painel.rename(columns={
        "Campanha":"Nome da Campanha",
        "Orçamento_atual":"Orçamento Atual",
        "ACOS_objetivo":"ACOS Objetivo Atual",
        "ROAS":"ROAS Real (calculado)",
        "Perda_orc":"% Perda Orçamento",
        "Perda_rank":"% Perda Classificação (rank)",
    })
    st.dataframe(painel, use_container_width=True)

    st.markdown("## Corte de Sangria em Produtos e Anúncios")
    cA, cB, cC = st.columns(3)
    with cA:
        st.markdown("**🔴 Sanguessugas**")
        st.dataframe(ads_meta["top_sanguessugas"][["MLB","Anúncio","Investimento","Receita","ROAS","ACOS_real"]], use_container_width=True)
    with cB:
        st.markdown("**🟡 Gastões**")
        st.dataframe(ads_meta["top_gastoes"][["MLB","Anúncio","Investimento","Receita","ROAS","ACOS_real"]], use_container_width=True)
    with cC:
        st.markdown("**🟢 Estrelas**")
        st.dataframe(ads_meta["top_estrelas"][["MLB","Anúncio","Investimento","Receita","ROAS","ACOS_real"]], use_container_width=True)

    if pub_out is not None:
        st.markdown("## Variações e Conversão (Publicações)")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**🟢 Melhores variações (CVR alto, min 20 visitas)**")
            st.dataframe(pub_meta["top_boas"][["Anúncio","Variação","Visitas","Vendas","CVR"]], use_container_width=True)
        with c2:
            st.markdown("**🔴 Piores variações (CVR baixo, min 20 visitas)**")
            st.dataframe(pub_meta["top_ruins"][["Anúncio","Variação","Visitas","Vendas","CVR"]], use_container_width=True)
