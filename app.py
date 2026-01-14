import streamlit as st
import pandas as pd

st.set_page_config(page_title="ML Ads", layout="wide")
st.title("ML Ads, limpeza automática do relatório")

arquivo = st.file_uploader(
    "Suba um relatório do Mercado Livre (CSV ou Excel)",
    type=["csv", "xlsx", "xls"]
)

def read_any(file):
    name = file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(file, header=None)
    return pd.read_excel(file, header=None, engine="openpyxl")

def detect_header_row(df_raw: pd.DataFrame) -> int:
    """
    Encontra a linha de cabeçalho real do Mercado Livre.
    Heurística: linha com mais células preenchidas e sem muitos números.
    """
    best_idx = 0
    best_score = -1

    # varre só as primeiras 30 linhas
    max_rows = min(len(df_raw), 30)

    for i in range(max_rows):
        row = df_raw.iloc[i].astype(str)

        # conta preenchidos
        filled = (row.str.strip() != "") & (row.str.lower() != "nan")
        filled_count = int(filled.sum())

        if filled_count == 0:
            continue

        # penaliza linhas muito numéricas
        numeric_like = row.str.match(r"^\s*[\d\.,%R$\-\s]+\s*$", na=False).sum()
        numeric_like = int(numeric_like)

        # score: muitos preenchidos, poucos numéricos
        score = filled_count - (numeric_like * 0.6)

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

def normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df

if arquivo:
    df_raw = read_any(arquivo)

    header_idx = detect_header_row(df_raw)
    st.info(f"Cabeçalho detectado na linha: {header_idx + 1}")

    # constrói df com cabeçalho correto
    header = df_raw.iloc[header_idx].astype(str).tolist()
    df = df_raw.iloc[header_idx + 1:].copy()
    df.columns = header
    df = df.reset_index(drop=True)
    df = normalize_df(df)

    # remove colunas totalmente vazias
    df = df.dropna(axis=1, how="all")

    st.success("Relatório limpo. Preview abaixo.")
    st.write(f"Linhas: {len(df):,} | Colunas: {df.shape[1]}")

    # tenta converter colunas numéricas automaticamente
    # estratégia: testa conversão, se converter mais de 70% vira numérica
    df2 = df.copy()
    for c in df2.columns:
        conv = clean_numeric_series(df2[c])
        ratio = conv.notna().mean()
        if ratio >= 0.70:
            df2[c] = conv

    st.markdown("### Preview (limpo)")
    st.dataframe(df2.head(50), use_container_width=True)

    st.markdown("### Colunas detectadas")
    st.write(list(df2.columns))
