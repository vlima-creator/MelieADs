import streamlit as st
import pandas as pd

st.set_page_config(page_title="ML Ads", layout="wide")
st.title("Teste de Upload e Leitura")

arquivo = st.file_uploader(
    "Suba um relatório (CSV ou Excel)",
    type=["csv", "xlsx", "xls"]
)

if arquivo:
    nome = arquivo.name.lower()

    if nome.endswith(".csv"):
        df = pd.read_csv(arquivo)
    else:
        df = pd.read_excel(arquivo, engine="openpyxl")

    st.success("Arquivo carregado com sucesso")
    st.write(f"Linhas: {len(df):,}")
    st.write(f"Colunas: {len(df.columns)}")

    st.dataframe(df.head(50), use_container_width=True)
