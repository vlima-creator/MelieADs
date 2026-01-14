import streamlit as st
import pandas as pd

st.set_page_config(page_title="ML Ads - Relatório Estratégico", layout="wide")
st.title("Mercado Livre Ads, Relatório Estratégico Automatizado")

BAD_HINTS = ["informações do relatório", "relatório de publicidade", "período", "moeda", "fuso"]

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
    header = df_raw.iloc[header_idx].astype(str).fillna("").tolist()

    df = df_raw.iloc[header_idx + 1:].copy()
    df.columns = [str(c).strip() for c in header]
    df = df.reset_index(drop=True)
    df = df.dropna(axis=1, how="all")
    df = df.loc[:, [c for c in df.columns if str(c).strip().lower() not in ["nan", ""]]]

    for c in df.columns:
        conv = clean_numeric_series(df[c])
        if conv.notna().mean() >= 0.70:
            df[c] = conv

    return df

def guess_type(df: pd.DataFrame) -> str:
    cols = " | ".join([c.lower() for c in df.columns])

    # Publicações
    if "id do anúncio" in cols or "visitas únicas" in cols or "conversão de visitas" in cols:
        return "publicacoes"

    # Campanhas
    if "nome da campanha" in cols or ("campanha" in cols and "orçamento" in cols):
        return "campanhas"

    # Anúncios patrocinados
    if "mlb" in cols and ("roas" in cols or "acos" in cols or "investimento" in cols):
        return "anuncios"

    return "desconhecido"

# ========= UI =========

period_label = st.text_input("Rótulo do período", value="Últimos 15 dias")

camp_file = st.file_uploader("1) Campanhas", type=["csv", "xlsx", "xls"])
ads_file = st.file_uploader("2) Anúncios patrocinados", type=["csv", "xlsx", "xls"])
pub_file = st.file_uploader("3) Publicações (opcional)", type=["csv", "xlsx", "xls"])

if st.button("Gerar relatório", type="primary", use_container_width=True):
    if camp_file is None or ads_file is None:
        st.error("Suba Campanhas e Anúncios patrocinados.")
        st.stop()

    with st.spinner("Lendo e validando..."):
        df_camp = ml_clean(camp_file)
        df_ads = ml_clean(ads_file)
        df_pub = ml_clean(pub_file) if pub_file else None

    t1 = guess_type(df_camp)
    t2 = guess_type(df_ads)

    if t1 != "campanhas":
        st.error(f"O arquivo 1 não parece ser Campanhas. Ele parece ser: {t1}. Suba o Relatorio_campanhas.")
        st.write("Colunas detectadas:", list(df_camp.columns))
        st.stop()

    if t2 != "anuncios":
        st.error(f"O arquivo 2 não parece ser Anúncios patrocinados. Ele parece ser: {t2}. Suba o Relatorio_anuncios_patrocinados.")
        st.write("Colunas detectadas:", list(df_ads.columns))
        st.stop()

    st.success("Arquivos corretos. Agora é só eu ligar a análise final em cima disso.")
    st.write("Campanhas colunas:", list(df_camp.columns))
    st.write("Anúncios colunas:", list(df_ads.columns))

    if df_pub is not None:
        st.info(f"Publicações detectado como: {guess_type(df_pub)}")
