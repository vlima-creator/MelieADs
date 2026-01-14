import re
import streamlit as st
import pandas as pd

st.set_page_config(page_title="ML Ads - Relatório Estratégico", layout="wide")
st.title("Mercado Livre Ads, Relatório Estratégico Automatizado")
st.caption("Suba os relatórios, clique em Gerar, receba decisões prontas.")

# =========================
# Helpers de leitura e limpeza
# =========================

BAD_HEADER_HINTS = [
    "informações do relatório",
    "informacoes do relatorio",
    "relatório de publicidade",
    "relatorio de publicidade",
    "período",
    "periodo",
    "moeda",
    "fuso",
]

def read_any(file):
    name = file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(file, header=None)
    return pd.read_excel(file, header=None, engine="openpyxl")

def detect_header_row(df_raw: pd.DataFrame) -> int:
    best_idx = 0
    best_score = -1
    max_rows = min(len(df_raw), 60)

    for i in range(max_rows):
        row = df_raw.iloc[i].astype(str).fillna("")
        row_l = row.str.lower().str.strip()

        # descarta linhas "de informação"
        if any(any(h in cell for h in BAD_HEADER_HINTS) for cell in row_l.tolist()):
            continue

        filled = (row_l != "") & (row_l != "nan")
        filled_count = int(filled.sum())
        if filled_count < 3:
            continue

        numeric_like = row_l.str.match(r"^\s*[\d\.,%R$\-\s]+\s*$", na=False).sum()
        numeric_like = int(numeric_like)

        # bônus se tem palavras que parecem colunas
        texty = row_l.str.contains(r"[a-záéíóúãõç]", regex=True, na=False).sum()
        texty = int(texty)

        score = (filled_count * 1.2) + (texty * 0.8) - (numeric_like * 1.0)

        if score > best_score:
            best_score = score
            best_idx = i

    return best_idx

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
         .str.replace(".", "", regex=False)    # milhar pt-br
         .str.replace(",", ".", regex=False)   # decimal pt-br
    )

    v = pd.to_numeric(x, errors="coerce")
    v = v.where(~is_percent, v / 100.0)
    return v.astype(float)

def ml_clean(file) -> pd.DataFrame:
    df_raw = read_any(file)

    header_idx = detect_header_row(df_raw)
    header = df_raw.iloc[header_idx].astype(str).fillna("").tolist()

    df = df_raw.iloc[header_idx + 1:].copy()
    df.columns = [str(c).strip() for c in header]
    df = df.reset_index(drop=True)

    # remove colunas vazias e colunas "nan"
    df = df.dropna(axis=1, how="all")
    df = df.loc[:, [c for c in df.columns if str(c).strip().lower() not in ["nan", ""]]]

    # remove linhas de "informação" que escaparem
    def row_is_info(row):
        txt = " ".join([str(x).lower() for x in row.values if str(x).lower() != "nan"])
        return any(h in txt for h in BAD_HEADER_HINTS)

    df = df[~df.apply(row_is_info, axis=1)].reset_index(drop=True)

    # converte numérico automaticamente
    for c in df.columns:
        conv = clean_numeric_series(df[c])
        if conv.notna().mean() >= 0.70:
            df[c] = conv

    return df

def colscore(name: str, patterns):
    n = name.lower()
    score = 0
    for p, w in patterns:
        if p in n:
            score += w
    return score

def pick_best_column(df: pd.DataFrame, patterns, numeric_required=False):
    best = None
    best_score = -1
    for c in df.columns:
        s = colscore(str(c), patterns)
        if s <= 0:
            continue
        if numeric_required and not pd.api.types.is_numeric_dtype(df[c]):
            # tenta converter
            conv = clean_numeric_series(df[c])
            if conv.notna().mean() < 0.70:
                continue
        if s > best_score:
            best_score = s
            best = c
    return best

def fmt_money(v):
    if v is None or pd.isna(v):
        return "-"
    return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def fmt_pct(v):
    if v is None or pd.isna(v):
        return "-"
    return f"{float(v)*100:.1f}%".replace(".", ",")

# =========================
# Análises
# =========================

def analyze_campaigns(df):
    # mapeamento automático por heurística
    col_name = pick_best_column(df, [
        ("nome da campanha", 10),
        ("campanha", 8),
        ("campaign", 6),
    ])

    col_spend = pick_best_column(df, [
        ("investimento", 10),
        ("gasto", 9),
        ("custo", 8),
        ("spend", 7),
    ], numeric_required=True)

    col_revenue = pick_best_column(df, [
        ("vendas por product ads", 12),
        ("receita", 10),
        ("vendas", 9),
        ("faturamento", 8),
        ("sales", 7),
    ], numeric_required=True)

    col_budget = pick_best_column(df, [
        ("orçamento médio diário", 10),
        ("orçamento diario", 9),
        ("orçamento", 8),
        ("orcamento", 8),
        ("budget", 6),
    ], numeric_required=True)

    col_acos_target = pick_best_column(df, [
        ("acos objetivo", 10),
        ("acos alvo", 9),
    ], numeric_required=True)

    col_loss_budget = pick_best_column(df, [
        ("perda por orçamento", 10),
        ("% perda orçamento", 9),
        ("loss budget", 7),
    ], numeric_required=True)

    col_loss_rank = pick_best_column(df, [
        ("perda por classificação", 10),
        ("% perda classificação", 9),
        ("perda por rank", 8),
        ("loss rank", 7),
    ], numeric_required=True)

    missing = [x for x in [col_name, col_spend, col_revenue] if x is None]
    if missing:
        return None, {
            "error": "Não consegui mapear automaticamente Nome da Campanha, Investimento e Receita.",
            "cols": list(df.columns),
        }

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

    has_orc = out["Perda_orc"].notna().any()
    has_rank = out["Perda_rank"].notna().any()

    escala_orc = (out["ROAS"] > 7) & (out["Perda_orc"] > 0.40) if has_orc else (out["ROAS"] > 8)
    competitividade = receita_relevante & (out["Perda_rank"] > 0.50) if has_rank else (receita_relevante & (out["ROAS"].between(3, 7)))
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
        "mapping": {
            "nome": col_name,
            "investimento": col_spend,
            "receita": col_revenue,
            "orcamento": col_budget,
            "acos_obj": col_acos_target,
            "perda_orc": col_loss_budget,
            "perda_rank": col_loss_rank,
        }
    }
    return out, meta

def analyze_sponsored_ads(df):
    def pick(name_patterns, numeric=False):
        return pick_best_column(df, name_patterns, numeric_required=numeric)

    col_mlb = pick([("mlb", 10), ("item id", 8), ("id do item", 8), ("id", 2)], numeric_required=False)
    col_title = pick([("título", 10), ("titulo", 10), ("anúncio", 9), ("anuncio", 9), ("item", 3)], numeric_required=False)
    col_spend = pick([("investimento", 10), ("gasto", 9), ("custo", 8), ("spend", 7)], numeric=True)
    col_revenue = pick([("receita", 10), ("vendas", 9), ("faturamento", 8), ("sales", 7)], numeric=True)
    col_roas = pick([("roas", 10)], numeric=True)
    col_acos = pick([("acos", 10)], numeric=True)

    if col_spend is None or col_revenue is None:
        return None, {"error": "Não consegui mapear Investimento e Receita no relatório de anúncios.", "cols": list(df.columns)}

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
# UI
# =========================

period_label = st.text_input("Rótulo do período", value="Últimos 15 dias")

camp_file = st.file_uploader("Campanhas", type=["csv", "xlsx", "xls"])
ads_file = st.file_uploader("Anúncios patrocinados", type=["csv", "xlsx", "xls"])

if "generated" not in st.session_state:
    st.session_state.generated = False

if st.button("Gerar relatório", type="primary", use_container_width=True):
    st.session_state.generated = True

if st.session_state.generated:
    if camp_file is None or ads_file is None:
        st.error("Suba os dois arquivos: Campanhas e Anúncios patrocinados.")
        st.stop()

    with st.spinner("Lendo e limpando arquivos..."):
        df_camp = ml_clean(camp_file)
        df_ads = ml_clean(ads_file)

    camp_out, camp_meta = analyze_campaigns(df_camp)
    if camp_out is None:
        st.error(camp_meta["error"])
        st.caption("Colunas detectadas no seu arquivo de Campanhas:")
        st.write(camp_meta["cols"])
        st.stop()

    ads_out, ads_meta = analyze_sponsored_ads(df_ads)
    if ads_out is None:
        st.error(ads_meta["error"])
        st.caption("Colunas detectadas no seu arquivo de Anúncios:")
        st.write(ads_meta["cols"])
        st.stop()

    # =========================
    # RELATÓRIO FINAL
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

    st.markdown("**Locomotivas**")
    st.dataframe(game[game["Quadrante"] == "COMPETITIVIDADE"][["Campanha","Receita","Investimento","ROAS","AÇÃO RECOMENDADA"]], use_container_width=True)

    st.markdown("**Minas limitadas**")
    st.dataframe(game[game["Quadrante"] == "ESCALA DE ORÇAMENTO"][["Campanha","Receita","Investimento","ROAS","AÇÃO RECOMENDADA"]], use_container_width=True)

    st.markdown("**Hemorragias**")
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
        st.write("- 🟢 Escale campanhas com ROAS alto.")

    st.markdown("**Dia 2 (Competir):**")
    if len(loco):
        for n in loco["Campanha"].tolist():
            st.write(f"- 🟡 Suba ACOS objetivo: {n}")
    else:
        st.write("- 🟡 Abra funil nas campanhas com volume e ROAS médio.")

    st.markdown("**Dia 3 (Estancar):**")
    if len(hemo):
        for n in hemo["Campanha"].tolist():
            st.write(f"- 🔴 Corte ou revise: {n}")
    else:
        st.write("- 🔴 Corte o que está abaixo do ROAS mínimo.")

    st.markdown("### 4. Painel Geral")
    painel = camp_out[["Campanha","Orçamento_atual","ACOS_objetivo","ROAS","Perda_orc","Perda_rank","AÇÃO RECOMENDADA"]]
    st.dataframe(painel, use_container_width=True)

    st.markdown("## Corte de Sangria (Anúncios patrocinados)")
    a, b, c = st.columns(3)
    with a:
        st.markdown("**🔴 Sanguessugas**")
        st.dataframe(ads_meta["top_sanguessugas"][["MLB","Anúncio","Investimento","Receita","ROAS","ACOS_real"]], use_container_width=True)
    with b:
        st.markdown("**🟡 Gastões**")
        st.dataframe(ads_meta["top_gastoes"][["MLB","Anúncio","Investimento","Receita","ROAS","ACOS_real"]], use_container_width=True)
    with c:
        st.markdown("**🟢 Estrelas**")
        st.dataframe(ads_meta["top_estrelas"][["MLB","Anúncio","Investimento","Receita","ROAS","ACOS_real"]], use_container_width=True)

    with st.expander("Diagnóstico técnico, mapeamento automático usado", expanded=False):
        st.write(camp_meta["mapping"])
