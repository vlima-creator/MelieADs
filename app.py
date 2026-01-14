import streamlit as st
import pandas as pd

st.set_page_config(page_title="ML Ads - Relatório Estratégico", layout="wide")
st.title("Mercado Livre Ads, Relatório Estratégico Automatizado")

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

def fmt_money(v):
    if v is None or pd.isna(v):
        return "-"
    return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def fmt_pct(v):
    if v is None or pd.isna(v):
        return "-"
    return f"{float(v)*100:.1f}%".replace(".", ",")

# =========================
# Análises com mapeamento manual
# =========================

def analyze_campaigns(df, col_name, col_spend, col_revenue, col_budget=None, col_acos_target=None, col_loss_budget=None, col_loss_rank=None):
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

    # Matriz CPI, com fallback se não tiver perda_orc/perda_rank
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
    # tenta achar colunas padrão, mas não trava se faltar título/mlb
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

    col_mlb = find_col(df, ["MLB", "Item ID", "ID do item", "ID"])
    col_title = find_col(df, ["Título do anúncio", "Titulo", "Anúncio", "Anuncio", "Item"])
    col_spend = find_col(df, ["Investimento", "Gasto", "Custo", "Spend"])
    col_revenue = find_col(df, ["Receita", "Vendas", "Sales", "Faturamento"])
    col_roas = find_col(df, ["ROAS", "ROAS real", "ROAS Real"])
    col_acos = find_col(df, ["ACOS", "ACOS real", "ACOS Real"])

    if col_spend is None or col_revenue is None:
        return None, "Anúncios patrocinados: preciso de Investimento e Receita."

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

f_camp = st.file_uploader("Campanhas", type=["csv", "xlsx", "xls"])
f_ads = st.file_uploader("Anúncios patrocinados", type=["csv", "xlsx", "xls"])

gerar = st.button("Gerar relatório", type="primary", use_container_width=True)

if gerar:
    if not f_camp or not f_ads:
        st.error("Preciso dos dois arquivos: Campanhas e Anúncios patrocinados.")
        st.stop()

    with st.spinner("Limpando e lendo arquivos..."):
        df_camp = ml_clean(f_camp)
        df_ads = ml_clean(f_ads)

    st.markdown("## Mapeamento de colunas, Campanhas")
    st.caption("Escolha quais colunas representam Nome, Investimento e Receita. Se existir, selecione orçamento e perdas.")

    cols = list(df_camp.columns)

    col_name = st.selectbox("Coluna Nome da Campanha", options=cols)
    col_spend = st.selectbox("Coluna Investimento/Gasto", options=cols)
    col_revenue = st.selectbox("Coluna Receita/Vendas", options=cols)

    optional = ["(nenhuma)"] + cols
    col_budget = st.selectbox("Coluna Orçamento (opcional)", options=optional, index=0)
    col_acos_target = st.selectbox("Coluna ACOS Objetivo (opcional)", options=optional, index=0)
    col_loss_budget = st.selectbox("Coluna Perda por Orçamento (opcional)", options=optional, index=0)
    col_loss_rank = st.selectbox("Coluna Perda por Rank (opcional)", options=optional, index=0)

    # trava para evitar processamento antes de selecionar
    confirmar = st.button("Confirmar mapeamento e gerar análise", type="secondary")

    if confirmar:
        def opt(v):
            return None if v == "(nenhuma)" else v

        camp_out, camp_meta = analyze_campaigns(
            df_camp,
            col_name=col_name,
            col_spend=col_spend,
            col_revenue=col_revenue,
            col_budget=opt(col_budget),
            col_acos_target=opt(col_acos_target),
            col_loss_budget=opt(col_loss_budget),
            col_loss_rank=opt(col_loss_rank),
        )

        ads_out, ads_meta = analyze_sponsored_ads(df_ads)
        if ads_out is None:
            st.error(ads_meta)
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
        for n in minas["Campanha"].tolist():
            st.write(f"- 🟢 Aumente orçamento: {n}") if len(minas) else st.write("- 🟢 Escale campanhas com ROAS alto.")

        st.markdown("**Dia 2 (Competir):**")
        for n in loco["Campanha"].tolist():
            st.write(f"- 🟡 Suba ACOS objetivo: {n}") if len(loco) else st.write("- 🟡 Abra funil nas campanhas com volume e ROAS médio.")

        st.markdown("**Dia 3 (Estancar):**")
        for n in hemo["Campanha"].tolist():
            st.write(f"- 🔴 Corte ou revise: {n}") if len(hemo) else st.write("- 🔴 Corte o que está abaixo do ROAS mínimo.")

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
