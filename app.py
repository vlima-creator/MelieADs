import streamlit as st
import pandas as pd

st.set_page_config(page_title="ML Ads - Relatório Estratégico", layout="wide")
st.title("Mercado Livre Ads, Relatório Estratégico Automatizado")
st.caption("Suba os relatórios, clique em Gerar, receba decisões prontas.")

BAD_HINTS = ["informações do relatório", "relatório de publicidade", "período", "moeda", "fuso"]

# =========================
# Leitura de arquivo (Excel escolhe melhor aba)
# =========================

def read_any(file):
    name = file.name.lower()

    if name.endswith(".csv"):
        return pd.read_csv(file, header=None)

    xls = pd.ExcelFile(file)
    best_df = None
    best_score = -1

    for sh in xls.sheet_names:
        df_try = pd.read_excel(xls, sheet_name=sh, header=None, engine="openpyxl")

        non_empty = df_try.notna().sum().sum()
        score = non_empty + (df_try.shape[1] * 50)

        sh_l = sh.lower()
        if "relat" in sh_l or "campanh" in sh_l or "anún" in sh_l or "anun" in sh_l:
            score += 5000

        if score > best_score:
            best_score = score
            best_df = df_try

    return best_df

# =========================
# Detectar header real
# =========================

def detect_header_row(df_raw: pd.DataFrame) -> int:
    best_idx = 0
    best_score = -1
    max_rows = min(len(df_raw), 60)

    for i in range(max_rows):
        row = df_raw.iloc[i].astype(str).fillna("")
        row_l = row.str.lower().str.strip()

        if any(any(h in cell for h in BAD_HINTS) for cell in row_l.tolist()):
            continue

        filled = (row_l != "") & (row_l != "nan")
        filled_count = int(filled.sum())
        if filled_count < 3:
            continue

        numeric_like = row_l.str.match(r"^\s*[\d\.,%R$\-\s]+\s*$", na=False).sum()
        texty = row_l.str.contains(r"[a-záéíóúãõç]", regex=True, na=False).sum()

        score = (filled_count * 1.2) + (int(texty) * 0.8) - (int(numeric_like) * 1.0)

        if score > best_score:
            best_score = score
            best_idx = i

    return best_idx

# =========================
# Colunas únicas e limpeza numérica
# =========================

def make_unique_columns(cols):
    seen = {}
    out = []
    for c in cols:
        base = str(c).strip()
        if base == "" or base.lower() == "nan":
            base = "col"
        if base not in seen:
            seen[base] = 0
            out.append(base)
        else:
            seen[base] += 1
            out.append(f"{base}__{seen[base]}")
    return out

def ensure_series(x):
    # Se for DataFrame (coluna duplicada), pega a primeira coluna
    if isinstance(x, pd.DataFrame):
        if x.shape[1] == 0:
            return pd.Series([pd.NA] * len(x))
        return x.iloc[:, 0]
    return x

def clean_numeric_series(s):
    s = ensure_series(s)

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
    header = df_raw.iloc[header_idx].astype(str).fillna("").tolist()

    df = df_raw.iloc[header_idx + 1:].copy()
    df.columns = make_unique_columns(header)
    df = df.reset_index(drop=True)

    df = df.dropna(axis=1, how="all")
    df = df.loc[:, [c for c in df.columns if str(c).strip().lower() not in ["nan", ""]]]

    # Converter numéricos automaticamente
    for c in list(df.columns):
        conv = clean_numeric_series(df[c])
        if conv.notna().mean() >= 0.70:
            df[c] = conv

    return df

# =========================
# Mapeamento automático
# =========================

def colscore(name, patterns):
    n = str(name).lower()
    score = 0
    for p, w in patterns:
        if p in n:
            score += w
    return score

def pick_best_column(df, patterns, numeric_required=False):
    best = None
    best_score = -1

    for c in df.columns:
        s = colscore(c, patterns)
        if s <= 0:
            continue

        if numeric_required:
            col = ensure_series(df[c])
            if not pd.api.types.is_numeric_dtype(col):
                conv = clean_numeric_series(col)
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
    col_name = pick_best_column(df, [
        ("nome da campanha", 10),
        ("campanha", 8),
        ("nome", 4),
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
        ("moeda local", 2),  # comum em "Receita (Moeda local)"
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
        ("acos", 4),
    ], numeric_required=True)

    col_loss_budget = pick_best_column(df, [
        ("perda por orçamento", 10),
        ("% perda orçamento", 9),
        ("loss budget", 7),
    ], numeric_required=True)

    col_loss_rank = pick_best_column(df, [
        ("perda por classificação", 10),
        ("perda por classificacao", 10),
        ("% perda classificação", 9),
        ("perda por rank", 8),
        ("loss rank", 7),
        ("rank", 2),
    ], numeric_required=True)

    if col_name is None or col_spend is None or col_revenue is None:
        return None, {
            "error": "Não consegui identificar colunas mínimas no relatório de campanhas. Preciso de Nome, Investimento e Receita.",
            "cols": list(df.columns),
        }

    out = pd.DataFrame()
    out["Campanha"] = ensure_series(df[col_name]).astype(str)
    out["Investimento"] = clean_numeric_series(df[col_spend])
    out["Receita"] = clean_numeric_series(df[col_revenue])

    out["Orçamento_atual"] = clean_numeric_series(df[col_budget]) if col_budget else pd.NA
    out["ACOS_objetivo"] = clean_numeric_series(df[col_acos_target]) if col_acos_target else pd.NA
    out["Perda_orc"] = clean_numeric_series(df[col_loss_budget]) if col_loss_budget else pd.NA
    out["Perda_rank"] = clean_numeric_series(df[col_loss_rank]) if col_loss_rank else pd.NA

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
    }
    return out, meta

def analyze_sponsored_ads(df):
    col_mlb = pick_best_column(df, [("mlb", 10), ("item id", 8), ("id do item", 8), ("id", 2)])
    col_title = pick_best_column(df, [("título", 10), ("titulo", 10), ("anúncio", 9), ("anuncio", 9), ("item", 3)])
    col_spend = pick_best_column(df, [("investimento", 10), ("gasto", 9), ("custo", 8), ("spend", 7)], numeric_required=True)
    col_revenue = pick_best_column(df, [("receita", 10), ("vendas", 9), ("faturamento", 8), ("sales", 7)], numeric_required=True)
    col_roas = pick_best_column(df, [("roas", 10)], numeric_required=True)
    col_acos = pick_best_column(df, [("acos", 10)], numeric_required=True)

    if col_spend is None or col_revenue is None:
        return None, {"error": "Não consegui mapear Investimento e Receita no relatório de anúncios.", "cols": list(df.columns)}

    out = pd.DataFrame()
    out["MLB"] = ensure_series(df[col_mlb]).astype(str) if col_mlb else "-"
    out["Anúncio"] = ensure_series(df[col_title]).astype(str) if col_title else "Anúncio"
    out["Investimento"] = clean_numeric_series(df[col_spend])
    out["Receita"] = clean_numeric_series(df[col_revenue])

    if col_roas:
        out["ROAS"] = clean_numeric_series(df[col_roas])
    else:
        out["ROAS"] = out["Receita"] / out["Investimento"].replace(0, pd.NA)

    if col_acos:
        out["ACOS_real"] = clean_numeric_series(df[col_acos])
    else:
        out["ACOS_real"] = out["Investimento"] / out["Receita"].replace(0, pd.NA)

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

period_label = st.text_input("Rótulo do período (opcional)", value="Últimos 15 dias")

camp_file = st.file_uploader("Relatório de Campanhas (Excel ou CSV)", type=["csv", "xlsx", "xls"])
ads_file = st.file_uploader("Relatório de Anúncios Patrocinados (Excel ou CSV)", type=["csv", "xlsx", "xls"])
pub_file = st.file_uploader("Relatório de Publicações (opcional)", type=["csv", "xlsx", "xls"])

if st.button("Gerar relatório", type="primary", use_container_width=True):
    if camp_file is None or ads_file is None:
        st.error("Suba os dois arquivos: Campanhas e Anúncios patrocinados.")
        st.stop()

    with st.spinner("Lendo e limpando arquivos..."):
        df_camp = ml_clean(camp_file)
        df_ads = ml_clean(ads_file)
        df_pub = ml_clean(pub_file) if pub_file else None

    with st.expander("Colunas detectadas (debug)", expanded=False):
        st.write("Campanhas:", list(df_camp.columns))
        st.write("Anúncios:", list(df_ads.columns))
        if df_pub is not None:
            st.write("Publicações:", list(df_pub.columns))

    camp_out, camp_meta = analyze_campaigns(df_camp)
    if camp_out is None:
        st.error(camp_meta["error"])
        st.write("Colunas detectadas:", camp_meta["cols"])
        st.stop()

    ads_out, ads_meta = analyze_sponsored_ads(df_ads)
    if ads_out is None:
        st.error(ads_meta["error"])
        st.write("Colunas detectadas:", ads_meta["cols"])
        st.stop()

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

    st.markdown("Locomotivas")
    st.dataframe(
        game[game["Quadrante"] == "COMPETITIVIDADE"][["Campanha", "Receita", "Investimento", "ROAS", "AÇÃO RECOMENDADA"]],
        use_container_width=True
    )

    st.markdown("Minas limitadas")
    st.dataframe(
        game[game["Quadrante"] == "ESCALA DE ORÇAMENTO"][["Campanha", "Receita", "Investimento", "ROAS", "AÇÃO RECOMENDADA"]],
        use_container_width=True
    )

    st.markdown("Hemorragias")
    st.dataframe(
        game[game["Quadrante"] == "HEMORRAGIA"][["Campanha", "Receita", "Investimento", "ROAS", "ACOS_real", "AÇÃO RECOMENDADA"]],
        use_container_width=True
    )

    st.markdown("### 3. Plano de Ação Tático (Próximos 7 Dias)")
    minas = game[game["Quadrante"] == "ESCALA DE ORÇAMENTO"].head(5)
    loco = game[game["Quadrante"] == "COMPETITIVIDADE"].head(5)
    hemo = game[game["Quadrante"] == "HEMORRAGIA"].head(5)

    st.markdown("Dia 1, destravar")
    if len(minas):
        for n in minas["Campanha"].tolist():
            st.write(f"- 🟢 Aumente orçamento: {n}")
    else:
        st.write("- 🟢 Escale campanhas com ROAS alto.")

    st.markdown("Dia 2, competir")
    if len(loco):
        for n in loco["Campanha"].tolist():
            st.write(f"- 🟡 Suba ACOS objetivo: {n}")
    else:
        st.write("- 🟡 Abra funil nas campanhas com volume e ROAS médio.")

    st.markdown("Dia 3, estancar")
    if len(hemo):
        for n in hemo["Campanha"].tolist():
            st.write(f"- 🔴 Corte ou revise: {n}")
    else:
        st.write("- 🔴 Corte o que está abaixo do ROAS mínimo.")

    st.markdown("### 4. Painel Geral")
    painel_cols = ["Campanha", "Orçamento_atual", "ACOS_objetivo", "ROAS", "Perda_orc", "Perda_rank", "AÇÃO RECOMENDADA"]
    st.dataframe(camp_out[painel_cols], use_container_width=True)

    st.markdown("## Corte de Sangria, Anúncios patrocinados")
    a, b, c = st.columns(3)
    with a:
        st.markdown("Sanguessugas")
        st.dataframe(ads_meta["top_sanguessugas"][["MLB", "Anúncio", "Investimento", "Receita", "ROAS", "ACOS_real"]], use_container_width=True)
    with b:
        st.markdown("Gastões")
        st.dataframe(ads_meta["top_gastoes"][["MLB", "Anúncio", "Investimento", "Receita", "ROAS", "ACOS_real"]], use_container_width=True)
    with c:
        st.markdown("Estrelas")
        st.dataframe(ads_meta["top_estrelas"][["MLB", "Anúncio", "Investimento", "Receita", "ROAS", "ACOS_real"]], use_container_width=True)
