import streamlit as st
import pandas as pd
import base64
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import re

import ml_report as ml
import os
import liquid_glass_components as lgc
import sales_funnel as sf
import marketplace_config as mkt
import shopee_report as shopee
import user_guide as ug
import engine_features as engine


# -------------------------
# Utilitários de Imagem
# -------------------------
def get_image_base64(path):
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

# -------------------------
# Formatadores BR
# -------------------------
def fmt_money_br(x):
    if pd.isna(x):
        return ""
    return f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_percent_br(x):
    if pd.isna(x):
        return ""
    return f"{x:.2f}%".replace(".", ",")


def fmt_number_br(x, decimals=2):
    if pd.isna(x):
        return ""
    return f"{x:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_int_br(x):
    if pd.isna(x):
        return ""
    try:
        return f"{int(round(float(x))):,}".replace(",", ".")
    except Exception:
        return ""


# -------------------------
# Estoque (opcional)
# -------------------------
def _digits_only(s) -> str:
    s = "" if s is None else str(s)
    return re.sub(r"\D", "", s)

def _norm_sku(s) -> str:
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return ""
    return str(s).strip().upper()

def load_stock_file(file) -> pd.DataFrame:
    """
    Lê o arquivo de estoque enviado pelo usuário.

    Arquivo base (Anuncios-....xlsx):
    - Aba: "Anúncios"
    - Coluna B: ITEM_ID (MLB)
    - Coluna D: SKU
    - Coluna G: QUANTITY (Estoque)

    Observação: esse arquivo costuma ter linhas de cabeçalho antes da tabela,
    por isso usamos skiprows para alinhar corretamente as colunas.
    """
    # Mantemos dtype=str para evitar conversões quebradas logo na leitura
    df = pd.read_excel(file, sheet_name="Anúncios", skiprows=4, dtype=str)

    # Preferência por nomes de coluna (mais seguro que posição)
    expected = {"ITEM_ID", "SKU", "QUANTITY"}
    if not expected.issubset(set(df.columns)):
        # fallback por posição (B, D, G) caso o ML mude o cabeçalho
        if df.shape[1] < 7:
            raise ValueError("Arquivo de estoque não tem colunas suficientes (precisa ter pelo menos até a coluna G).")
        df = df.iloc[:, [1, 3, 6]].copy()
        df.columns = ["ITEM_ID", "SKU", "QUANTITY"]

    df = df[["ITEM_ID", "SKU", "QUANTITY"]].copy()

    # Filtra linhas válidas
    df["ITEM_ID"] = df["ITEM_ID"].astype(str).str.strip()
    df = df[df["ITEM_ID"].str.contains("MLB", na=False)]

    # Normaliza chaves
    df["MLB_key"] = df["ITEM_ID"].map(_digits_only)
    df["SKU_key"] = df["SKU"].map(_norm_sku)

    # Estoque como inteiro
    df["Estoque"] = pd.to_numeric(df["QUANTITY"], errors="coerce").fillna(0).astype(int)

    # Dedup: mantém o maior estoque por MLB
    df = df.sort_values("Estoque", ascending=False).drop_duplicates(subset=["MLB_key"], keep="first")

    return df[["MLB_key", "SKU_key", "Estoque"]]

def enrich_with_stock(df: pd.DataFrame, stock_df: pd.DataFrame) -> pd.DataFrame:
    """
    Enriquecimento por:
    1) MLB (preferência)
    2) SKU (fallback)
    """
    if df is None or df.empty:
        return df
    if stock_df is None or stock_df.empty:
        out = df.copy()
        if "Estoque" not in out.columns:
            out["Estoque"] = pd.NA
        return out

    out = df.copy()

    # Chaves no dataframe principal
    # Preferimos Codigo_MLB (MLBxxxxxxxx) e depois ID
    if "Codigo_MLB" in out.columns:
        out["MLB_key"] = out["Codigo_MLB"].map(_digits_only)
    elif "ID" in out.columns:
        out["MLB_key"] = out["ID"].map(_digits_only)
    else:
        out["MLB_key"] = ""

    if "SKU" in out.columns:
        out["SKU_key"] = out["SKU"].map(_norm_sku)
    else:
        out["SKU_key"] = ""

    # 1) Merge por MLB_key
    out = out.merge(
        stock_df[["MLB_key", "Estoque"]].drop_duplicates("MLB_key"),
        how="left",
        on="MLB_key",
        suffixes=("", "_stk"),
    )

    # 2) Fallback por SKU_key para quem ficou sem estoque
    miss = out["Estoque"].isna()
    if miss.any():
        sku_map = (
            stock_df[stock_df["SKU_key"].astype(str).str.len() > 0]
            .drop_duplicates(subset=["SKU_key"])
            .set_index("SKU_key")["Estoque"]
        )
        out.loc[miss, "Estoque"] = out.loc[miss, "SKU_key"].map(sku_map)

    out["Estoque"] = pd.to_numeric(out["Estoque"], errors="coerce")
    return out

def apply_stock_rules(enter_df: pd.DataFrame, scale_df: pd.DataFrame, acos_df: pd.DataFrame, pause_df: pd.DataFrame, *,
                      estoque_min_ads: int, estoque_baixo: int, estoque_critico: int, tratar_estoque_vazio_como_zero: bool):
    """Ajusta apenas para exibicao: bloqueia entrar em Ads por estoque e marca freio em campanhas."""
    blocked = pd.DataFrame()

    def _stock_value(s):
        if s is None or (isinstance(s, float) and pd.isna(s)):
            return 0 if tratar_estoque_vazio_como_zero else None
        try:
            return float(s)
        except Exception:
            return 0 if tratar_estoque_vazio_como_zero else None

    def _status(v):
        if v is None:
            return "SEM_ESTOQUE"
        if v <= 0:
            return "ZERADO"
        if v <= estoque_critico:
            return "CRITICO"
        if v <= estoque_baixo:
            return "BAIXO"
        return "OK"

    def _add_status(df):
        if df is None or df.empty:
            return df
        df2 = df.copy()
        if "Estoque" not in df2.columns:
            df2["Estoque"] = pd.NA
        df2["Estoque_Status"] = df2["Estoque"].map(_stock_value).map(_status)
        return df2

    enter2 = _add_status(enter_df)
    scale2 = _add_status(scale_df)
    acos2  = _add_status(acos_df)
    pause2 = _add_status(pause_df)

    # Bloquear "Entrar em Ads" se estoque insuficiente
    if enter2 is not None and not enter2.empty and "Estoque" in enter2.columns:
        v = enter2["Estoque"].map(_stock_value)
        mask_block = v.notna() & (v < float(estoque_min_ads))
        if mask_block.any():
            blocked = enter2.loc[mask_block].copy()
            blocked["Motivo_Estoque"] = "Estoque abaixo do minimo para entrar em Ads"
            enter2 = enter2.loc[~mask_block].copy()

    # Marcar freio nas tabelas de escala/ROAS se estoque baixo/critico
    def _mark_freio(df):
        if df is None or df.empty or "Estoque" not in df.columns:
            return df
        df3 = df.copy()
        v = df3["Estoque"].map(_stock_value)
        mask_crit = v.notna() & (v <= float(estoque_critico))
        mask_low  = v.notna() & (v > float(estoque_critico)) & (v <= float(estoque_baixo))
        if "Acao_Recomendada" in df3.columns:
            df3.loc[mask_crit, "Acao_Recomendada"] = "FREAR, ESTOQUE CRITICO"
            df3.loc[mask_low,  "Acao_Recomendada"] = "FREAR, ESTOQUE BAIXO"
        if "Motivo" in df3.columns:
            df3.loc[mask_crit, "Motivo"] = (df3.loc[mask_crit, "Motivo"].astype(str).str.strip() + " | estoque critico")
            df3.loc[mask_low,  "Motivo"] = (df3.loc[mask_low,  "Motivo"].astype(str).str.strip() + " | estoque baixo")
        return df3

    scale2 = _mark_freio(scale2)
    acos2  = _mark_freio(acos2)

    return enter2, scale2, acos2, pause2, blocked

# -------------------------
# Limpeza e ordenacao das tabelas (APENAS VISUAL)
# -------------------------


def _norm_col(col: str) -> str:
    return str(col).strip().lower().replace(' ', '_').replace('__', '_')


def _drop_cols_by_norm(df: pd.DataFrame, targets_norm: set[str]) -> pd.DataFrame:
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return df
    drop_cols = [c for c in df.columns if _norm_col(c) in targets_norm]
    return df.drop(columns=drop_cols, errors='ignore')


def _keep_first_by_prefix(df: pd.DataFrame, prefixes_norm: tuple[str, ...]) -> pd.DataFrame:
    """Mantem apenas a primeira coluna cujo nome normalizado inicia com algum prefixo informado."""
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return df
    cols = list(df.columns)
    hits = [c for c in cols if any(_norm_col(c).startswith(p) for p in prefixes_norm)]
    if len(hits) <= 1:
        return df
    # mantem a primeira na ordem atual
    for col in hits[1:]:
        df = df.drop(columns=[col], errors='ignore')
    return df


def _reorder_next_to(df: pd.DataFrame, left_col: str, right_col: str) -> pd.DataFrame:
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return df
    if left_col not in df.columns or right_col not in df.columns:
        return df
    cols = list(df.columns)
    cols.remove(right_col)
    try:
        idx = cols.index(left_col) + 1
    except ValueError:
        return df
    cols.insert(idx, right_col)
    return df[cols]


def _enforce_action_block(df: pd.DataFrame) -> pd.DataFrame:
    """Garante Acao_Recomendada antes de Confianca_Dado e Motivo, sem baguncar o resto."""
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return df
    ordered = []
    for col in ["Acao_Recomendada", "Confianca_Dado", "Motivo"]:
        if col in df.columns:
            ordered.append(col)
    if not ordered:
        return df
    rest = [c for c in df.columns if c not in ordered]
    # insere o bloco no fim do rest, mas mantendo a ordem do bloco
    return df[rest + ordered]


def _reorder_roas_acos(df: pd.DataFrame) -> pd.DataFrame:
    """
    Regras visuais:
    - manter apenas 1 ROAS objetivo (quando houver duplicatas)
    - colar ROAS_Real ao lado do ROAS objetivo
    - colar ACOS_Real ao lado do ROAS_Real (logo depois)
    """
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return df

    # 1) manter apenas o primeiro ROAS objetivo (variações)
    df = _keep_first_by_prefix(df, prefixes_norm=("roas_objetivo", "roas_objetivo_n", "roas_objetivo"))

    # detectar a coluna de ROAS objetivo que sobrou
    roas_obj_cols = [c for c in df.columns if _norm_col(c).startswith('roas_objetivo')]
    roas_obj_col = roas_obj_cols[0] if roas_obj_cols else None

    # detectar ROAS real e ACOS real (variações)
    roas_real_cols = [c for c in df.columns if _norm_col(c) == 'roas_real']
    roas_real_col = roas_real_cols[0] if roas_real_cols else None

    acos_real_cols = [c for c in df.columns if _norm_col(c) == 'acos_real']
    acos_real_col = acos_real_cols[0] if acos_real_cols else None

    # 2) posicionar ROAS_Real logo após ROAS objetivo (se existir)
    if roas_obj_col and roas_real_col:
        df = _reorder_next_to(df, roas_obj_col, roas_real_col)

    # 3) posicionar ACOS_Real logo após ROAS_Real
    if roas_real_col and acos_real_col:
        df = _reorder_next_to(df, roas_real_col, acos_real_col)

    return df


def prepare_df_for_view(df: pd.DataFrame, *, drop_cpi_cols: bool = True, drop_roas_generic: bool = False) -> pd.DataFrame:
    """
    Aplica padroes de visualizacao sem alterar calculos:
    - (opcional) remove CPI_Share, CPI_Cum, CPI_80
    - (opcional) remove ROAS generico (coluna 'ROAS')
    - remove duplicatas de ROAS objetivo, cola ROAS_Real e ACOS_Real
    - garante Acao_Recomendada antes de Confianca_Dado e Motivo
    """
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return df

    out = df.copy()

    if drop_cpi_cols:
        out = _drop_cols_by_norm(out, targets_norm={"cpi_share", "cpi_cum", "cpi_80"})

    if drop_roas_generic:
        out = _drop_cols_by_norm(out, targets_norm={"roas"})

    out = _reorder_roas_acos(out)
    out = _enforce_action_block(out)
    return out
# -------------------------
# Detectores de colunas
# -------------------------
def _is_money_col(col_name: str) -> bool:
    c = str(col_name).strip().lower()
    money_keys = [
        "orcamento",
        "orçamento",
        "investimento",
        "receita",
        "vendas_brutas",
        "potencial_receita",
        "potencial receita",
        "impacto_estimado",
        "impacto estimado",
        "faturamento",
        "vendas (r$)",
        "invest",
        "invest_campanha",
        "receita_campanha",
    ]
    return any(k in c for k in money_keys)


def _is_id_col(col_name: str) -> bool:
    """
    IDs sao identificadores, nao devem receber formatacao numerica.
    Mantem como texto puro (ex: 6086561266).
    """
    c = str(col_name).strip().lower().replace("__", "_")
    return (
        c == "id"
        or c == "id_anuncio"
        or c == "id_anúncio"
        or c == "id campanha"
        or c == "id_campanha"
        or c.endswith("_id")
        or c.startswith("id_")
        or "id anuncio" in c
        or "id anúncio" in c
        or "id do anuncio" in c
        or "id do anúncio" in c
        or "id campanha" in c
        or c == "mlb_key"
        or c == "codigo_mlb"
        or c == "código_mlb"
        or c == "item_id"
        or c == "item id"
        or c.startswith("mlb")
        or "mlb" in c
    )


# IMPORTANTE
# Tiramos ACOS objetivo e ACOS_Objetivo_N daqui, porque agora viram ROAS (numero)
_PERCENT_COLS = {
    "acos real",
    "acos_real",
    "cpi_share",
    "cpi share",
    "cpi_cum",
    "cpi cum",
    "con_visitas_vendas",
    "con visitas vendas",
    "conv_visitas_vendas",
    "conv visitas vendas",
    "conv_visitas_compradores",
    "conv visitas compradores",
    "perdidas_orc",
    "perdidas_class",
    "cvr",
    "cvr\n(conversion rate)",
}


def _is_percent_col(col_name: str) -> bool:
    c = str(col_name).strip().lower().replace("__", "_")
    if c in _PERCENT_COLS:
        return True
    # padrões comuns do app (ex: ctr_pct, cvr_campanha_pct, pct_invest_campanha)
    return c.endswith("_pct") or c.startswith("pct_") or ("_pct_" in c)



def _is_count_col(col_name: str) -> bool:
    """
    Apenas colunas de volume/contagem, para remover decimais.
    Evita capturar colunas de conversao/taxa (Conv_Visitas_Vendas etc).
    """
    c = str(col_name).strip().lower().replace("__", "_")

    # nunca formatar como inteiro se for conversao/taxa
    if (
        "conv_" in c
        or c.startswith("con_")
        or "convers" in c
        or "cvr" in c
        or "taxa" in c
    ):
        return False

    targets = {
        "impressoes",
        "impressões",
        "impressions",
        "cliques",
        "clicks",
        "visitas",
        "visits",
        "qtd_vendas",
        "qtd vendas",
        "quantidade_vendas",
        "quantidade vendas",
        "orders",
        "pedidos",
        "estoque",
        "stock",
    }

    if c in targets:
        return True

    # casos com sufixo
    if c.endswith("_impressoes") or c.endswith("_impressões") or c.endswith("_impressions"):
        return True
    if c.endswith("_cliques") or c.endswith("_clicks"):
        return True
    if c.endswith("_visitas") or c.endswith("_visits"):
        return True
    if "qtd_vendas" in c or "quantidade_vendas" in c:
        return True

    return False


# -------------------------
# ACOS objetivo -> ROAS objetivo (inclui ACOS_Objetivo_N)
# -------------------------
def _acos_value_to_roas(ac):
    if pd.isna(ac):
        return pd.NA
    try:
        v = float(ac)
    except Exception:
        return pd.NA

    if v == 0:
        return pd.NA

    # se vier como percentual (25, 30, 50), converte para fracao
    acos_frac = v / 100 if v > 2 else v
    if acos_frac <= 0:
        return pd.NA

    return 1 / acos_frac


def _roas_col_name_from_acos_col(col_name: str) -> str:
    lc = str(col_name).strip().lower().replace("__", "_")
    if lc.endswith("_n") or "objetivo_n" in lc or "objetivo n" in lc:
        return "ROAS objetivo N"
    return "ROAS objetivo"


def replace_acos_obj_with_roas_obj(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converte TODAS as colunas que tenham "acos" e "objetivo":
    - ACOS Objetivo -> ROAS objetivo
    - ACOS_Objetivo_N -> ROAS objetivo N
    Mantem ambas se existirem no dataframe.
    """
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return df

    df2 = df.copy()
    renames = {}

    for col in list(df2.columns):
        lc = str(col).strip().lower()
        if "acos" in lc and "objetivo" in lc:
            ser = pd.to_numeric(df2[col], errors="coerce")
            df2[col] = ser.map(_acos_value_to_roas)
            renames[col] = _roas_col_name_from_acos_col(col)

    if renames:
        df2 = df2.rename(columns=renames)

    return df2


# -------------------------
# Formatacao unificada (Painel, CPI, Acoes)
# -------------------------
def format_table_br(df: pd.DataFrame) -> pd.DataFrame:
    """
    Regras:
    - preserva colunas de texto (Nome da campanha, Acao_recomendada, etc)
    - IDs: texto puro (somente digitos)
    - dinheiro: R$ com separador BR
    - percentuais: % com separador BR (e escala corrigida se vier 0-1)
    - contagens: inteiros sem decimais (Impressoes, Cliques, Visitas, Qtd_Vendas)
    - numeros gerais: 2 casas e separador BR
    """
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return df

    df_fmt = df.copy()

    for col in df_fmt.columns:
        lc = str(col).strip().lower()

        # IDs devem ser texto puro, sem formatacao numerica
        if _is_id_col(col):
            s = df_fmt[col].astype(str).replace({"nan": ""})
            # remove .0, separadores e qualquer caractere nao numerico
            s = s.str.replace(r"\.0$", "", regex=True)
            s = s.str.replace(r"\D", "", regex=True)
            df_fmt[col] = s
            continue

        # preserva texto por nome (blindagem)
        if (
            "nome" in lc
            or "campanha" in lc
            or "acao" in lc
            or "ação" in lc
            or "recomend" in lc
            or "estrateg" in lc
            or "estratég" in lc
        ):
            df_fmt[col] = df_fmt[col].astype(str).replace({"nan": ""})
            continue

        serie_num = pd.to_numeric(df_fmt[col], errors="coerce")
        non_null = df_fmt[col].notna().sum()
        num_ok = serie_num.notna().sum()

        # se nao for numerica, preserva como texto
        if non_null == 0 or (num_ok / max(non_null, 1)) < 0.60:
            df_fmt[col] = df_fmt[col].astype(str).replace({"nan": ""})
            continue

        # ordem importa: percentual antes de contagem
        if _is_money_col(col):
            df_fmt[col] = serie_num.map(fmt_money_br)

        elif _is_percent_col(col):
            # Percentuais (Conv_Visitas_Vendas, CVR, Perdidas etc) já estão em pontos percentuais
            # (ex: 1.19 significa 1,19%). Não aplicar auto-escala por heurística.
            df_fmt[col] = serie_num.map(fmt_percent_br)

        elif _is_count_col(col):
            df_fmt[col] = serie_num.map(fmt_int_br)

        else:
            df_fmt[col] = serie_num.map(lambda x: fmt_number_br(x, 2))

    return df_fmt


# -------------------------
# App
# -------------------------
def render_pareto_chart(df):
    """Gera um gráfico de Pareto para a Receita das Campanhas."""
    if df is None or df.empty or "Receita" not in df.columns:
        return
    
    df_sorted = df.sort_values("Receita", ascending=False).copy()
    df_sorted["Receita_Cum_Pct"] = 100 * df_sorted["Receita"].cumsum() / df_sorted["Receita"].sum()
    
    fig = go.Figure()
    
    # Barras de Receita
    fig.add_trace(go.Bar(
        x=df_sorted["Nome"],
        y=df_sorted["Receita"],
        name="Receita",
        marker_color="#3483fa"
    ))
    
    # Linha de Percentual Acumulado
    fig.add_trace(go.Scatter(
        x=df_sorted["Nome"],
        y=df_sorted["Receita_Cum_Pct"],
        name="% Acumulado",
        yaxis="y2",
        line=dict(color="#ffe600", width=3),
        mode="lines+markers"
    ))
    
    fig.update_layout(
        title="Análise de Pareto: Receita por Campanha",
        xaxis=dict(title="Campanha", showticklabels=False),
        yaxis=dict(title="Receita (R$)"),
        yaxis2=dict(title="% Acumulado", overlaying="y", side="right", range=[0, 110]),
        template="plotly_dark",
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)

def render_treemap_chart(df):
    """Gera um Treemap mostrando Investimento por Campanha, agrupado por Quadrante e colorido por ROAS."""
    if df is None or df.empty or "Investimento" not in df.columns:
        return
    
    df_plot = df[df["Investimento"] > 0].copy()
    
    # Preparar dados para o Treemap
    df_plot["ROAS_Real"] = pd.to_numeric(df_plot.get("ROAS_Real", 0), errors="coerce").fillna(0)
    df_plot["Quadrante"] = df_plot.get("Quadrante", "SEM_CLASSIFICACAO")
    
    # Criar figura com Treemap usando path e values
    fig = px.treemap(
        df_plot,
        path=["Quadrante", "Nome"],
        values="Investimento",
        color="ROAS_Real",
        color_continuous_scale="RdYlGn",
        title="Distribuição de Investimento por Quadrante"
    )
    fig.update_layout(
        template="plotly_dark",
        margin=dict(l=10, r=10, t=40, b=10)
    )
    st.plotly_chart(fig, use_container_width=True)

def render_funnel_chart(kpis):
    """Gera um gráfico de funil moderno, estético e minimalista."""
    if not kpis:
        return
        
    # Extração de dados
    imp = float(kpis.get("Impressões Totais", 0))
    clk = float(kpis.get("Cliques Totais", 0))
    vendas = float(kpis.get("Vendas Ads", 0))
    
    if imp == 0:
        return

    # Cálculo de taxas
    ctr = (clk / imp * 100) if imp > 0 else 0
    cvr = (vendas / clk * 100) if clk > 0 else 0
    
    # Dados para o funil (Estético: larguras fixas para evitar design estranho)
    stages = ["Impressões", "Cliques", "Vendas"]
    
    # Cores modernas (Escala de cinzas profissionais com destaque sutil)
    colors = ["#2C3E50", "#34495E", "#1ABC9C"] # Azul escuro SaaS para o topo, Verde suave para conversão final
    
    fig = go.Figure(go.Funnel(
        y = stages,
        x = [100, 75, 50], # Larguras fixas para estética moderna
        textinfo = "text",
        text = [
            f"<span style='font-size:14px; font-weight:bold;'>{stages[0]}</span><br><span style='font-size:18px;'>{fmt_int_br(imp)}</span>",
            f"<span style='font-size:14px; font-weight:bold;'>{stages[1]}</span><br><span style='font-size:18px;'>{fmt_int_br(clk)}</span><br><span style='font-size:12px; color:#BDC3C7;'>CTR: {ctr:.2f}%</span>",
            f"<span style='font-size:14px; font-weight:bold;'>{stages[2]}</span><br><span style='font-size:18px;'>{fmt_int_br(vendas)}</span><br><span style='font-size:12px; color:#BDC3C7;'>CVR: {cvr:.2f}%</span>"
        ],
        marker = {
            "color": colors,
            "line": {"width": [2, 2, 2], "color": "white"}
        },
        connector = {"line": {"color": "#7F8C8D", "width": 1, "dash": "dot"}}
    ))
    
    fig.update_layout(
        title_text = "Funil de Conversão Estratégico",
        title_font = dict(size=20, color="#ECF0F1"),
        title_x = 0.5,
        margin = dict(l=150, r=150, t=80, b=40), # Mais margem lateral para o funil não ficar "esticado"
        height = 450,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        template="plotly_dark"
    )
    
    # Remove eixos para ficar minimalista
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False) # Remove nomes laterais para usar o texto interno
    
    st.plotly_chart(fig, use_container_width=True)

def main():
    st.set_page_config(page_title="AdsEngine", layout="wide", initial_sidebar_state="expanded")

    # Carregar CSS customizado
    try:
        with open(".streamlit/style.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("Arquivo de estilo não encontrado. O dashboard será exibido com o tema padrão.")

    with st.sidebar:
        st.markdown("### 🏪 Selecionar Marketplace")
        
        marketplace_options = mkt.get_marketplace_list()
        marketplace_keys = [key for key, _, _ in marketplace_options]
        
        selected_marketplace = st.selectbox(
            "Canal de Vendas",
            options=marketplace_keys,
            format_func=lambda x: mkt.get_marketplace_config(x)['name'],
            index=0,
            label_visibility="collapsed"
        )
        
        # Exibir logo dinâmico baseado no marketplace
        logo_configs = {
            "mercado_livre": {"path": "assets/mercado_livre_logo_transparent.png", "color": "#ffe600", "size": "55px"},
            "shopee": {"path": "assets/shopee_logo_transparent.png", "color": "#ee4d2d", "size": "55px"}
        }
        
        if selected_marketplace in logo_configs:
            config = logo_configs[selected_marketplace]
            logo_base64 = get_image_base64(config["path"])
            if logo_base64:
                st.markdown(
                    f"""
                    <div style="display: flex; justify-content: center; margin: 15px 0;">
                        <div style="background: {config['color']}; padding: 12px; border-radius: 50%; width: 80px; height: 80px; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 12px rgba(0,0,0,0.3);">
                            <img src="data:image/png;base64,{logo_base64}" width="{config['size']}">
                        </div>
                    </div>
                    <h3 style="text-align: center; margin-top: 0;">{mkt.get_marketplace_config(selected_marketplace)['name']}</h3>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.markdown(f"### {mkt.get_marketplace_config(selected_marketplace)['icon']} {mkt.get_marketplace_config(selected_marketplace)['name']}")
        else:
            st.markdown(f"### {mkt.get_marketplace_config(selected_marketplace)['icon']} {mkt.get_marketplace_config(selected_marketplace)['name']}")
        
        marketplace_config = mkt.get_marketplace_config(selected_marketplace)
        
        st.divider()
        st.caption(f"Atualizado em {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        st.divider()
        st.markdown(
            """
            <div style='font-size: 0.8em; color: #888888;'>
                © Desenvolvido por Vinicius Lima / CNPJ: 47.192.694/0001-70
            </div>
            """,
            unsafe_allow_html=True
        )
        st.divider()
    
    st.title("AdsEngine")
    st.markdown("<h3 style='text-align: center; color: #00C853;'>Otimização Inteligente para Campanhas de Alta Performance</h3>", unsafe_allow_html=True)

    # Título dinâmico baseado no marketplace

    selected_page = st.sidebar.radio(
        "Navegação",
        ["Dashboard", "Guia de Uso"],
        format_func=lambda x: f"📊 {x}" if x == "Dashboard" else f"📖 {x}"
    )

    if selected_page == "Guia de Uso":
        ug.render_user_guide()
        return
    
    # Título do Dashboard com Logo Dinâmico
    header_configs = {
        "mercado_livre": {"path": "assets/mercado_livre_logo_transparent.png", "color": "#ffe600"},
        "shopee": {"path": "assets/shopee_logo_transparent.png", "color": "#ee4d2d"}
    }
    
    if selected_marketplace in header_configs:
        config = header_configs[selected_marketplace]
        logo_base64 = get_image_base64(config["path"])
        if logo_base64:
            st.markdown(
                f"""
                <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 25px; background: rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 12px; border-left: 5px solid {config['color']};">
                    <div style="background: {config['color']}; padding: 8px; border-radius: 50%; width: 50px; height: 50px; display: flex; align-items: center; justify-content: center;">
                        <img src="data:image/png;base64,{logo_base64}" width="35">
                    </div>
                    <h1 style="margin: 0; font-size: 1.8rem;">{marketplace_config['name']} <span style="color: #888; font-weight: 300;">| Dashboard</span></h1>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.title(f"{marketplace_config['icon']} {marketplace_config['name']} - Dashboard")
    else:
        st.title(f"{marketplace_config['icon']} {marketplace_config['name']} - Dashboard")

    with st.sidebar:
        
        with st.expander("📖 Guia: Como obter os relatórios", expanded=False):
            st.markdown("""
            ### 1. Relatório de Campanhas
            **Caminho:** 	
            Publicidade > Relatórios > Tipo de Relatório: Campanhas (Padrão) > Selecionar Período > Agrupamento de Dados: Total do Período.
            
            *Este arquivo traz o resumo consolidado das suas campanhas.*

            ### 2. Anúncios Patrocinados
            **Caminho:** 
            Publicidade > Relatórios > Tipo de Relatório: Anúncios (Padrão) > Selecionar Período > Agrupamento de Dados: Total do Período.
            
            *Este arquivo detalha a performance de cada anúncio dentro do Ads.*

            ### 3. Desempenho de Anúncios
            **Caminho:** 
            Métricas > Selecionar o Período > Descer até a sessão Desempenho de anúncios > Baixar relatório > Desempenho dos seus anúncios.
            
            *Este arquivo é essencial para compararmos o que vende no orgânico vs. pago.*

            ### 4. Relatório de Inventário
            **Caminho:** 
            Anúncios > Alterar pelo Excel > Condições Gerais > Baixar o Excel do Inventário > Selecione os anúncios que você vai baixar > Categorias: Todos > Baixar.
            
            *Este arquivo é opcional para analisarmos as campanhas com base no estoque*
            
            ---
            **Dica:** Baixe sempre o período de **Últimos 30 dias** ou **Mês Anterior** para uma análise mais robusta.
            """)

        st.divider()

        st.subheader("📁 Arquivos Obrigatórios")
        
        # Upload dinâmico baseado no marketplace
        uploaded_files = {}
        organico_file = None
        patrocinados_file = None
        campanhas_file = None
        camp_agg = pd.DataFrame()
        
        if selected_marketplace == "mercado_livre":
            organico_file = st.file_uploader("Relatorio de Desempenho de Anúncios (Excel)", type=["xlsx"])
            patrocinados_file = st.file_uploader("Relatorio Anuncios Patrocinados (Excel)", type=["xlsx"])
            campanhas_file = st.file_uploader("Relatorio de Campanha (Excel)", type=["xlsx"])
            uploaded_files = {
                "vendas": organico_file,
                "patrocinados": patrocinados_file,
                "campanha": campanhas_file
            }
        elif selected_marketplace == "shopee":
            dados_gerais_file = st.file_uploader(
                "Dados Gerais de Anúncios (CSV)",
                type=["csv"],
                help="Relatório de Todos os Anúncios CPC da Shopee"
            )
            uploaded_files = {
                "dados_gerais": dados_gerais_file
            }
        
        st.divider()
        st.subheader("📂 Arquivos Opcionais")
        
        if selected_marketplace == "mercado_livre":
            snapshot_file = st.file_uploader(
                "Snapshot de Referencia (Excel)",
                type=["xlsx"],
                help="Arquivo gerado ha 15 dias para comparar evolucao (Snapshot v2)"
            )
            uploaded_files["snapshot"] = snapshot_file
            
            usar_estoque = st.checkbox("Ativar visão de estoque", value=False)
            estoque_file = st.file_uploader("Arquivo de estoque (Excel)", type=["xlsx"], disabled=not usar_estoque)
            uploaded_files["estoque"] = estoque_file if usar_estoque else None
            
            if usar_estoque:
                cA, cB, cC = st.columns(3)
                with cA:
                    estoque_min_ads = st.number_input("Mínimo p/ entrar em Ads (un)", min_value=0, value=6, step=1)
                with cB:
                    estoque_baixo = st.number_input("Estoque baixo (un)", min_value=0, value=6, step=1)
                with cC:
                    estoque_critico = st.number_input("Estoque crítico (un)", min_value=0, value=2, step=1)
                tratar_estoque_vazio_como_zero = st.checkbox("Tratar estoque ausente como zero", value=False)
            else:
                estoque_min_ads = 6
                estoque_baixo = 6
                estoque_critico = 2
                tratar_estoque_vazio_como_zero = False
                
        elif selected_marketplace == "shopee":
            palavras_chave_file = st.file_uploader(
                "Relatório de Palavras-chave (CSV)",
                type=["csv"],
                help="Relatório de Anúncio + Palavra-chave + Locação (opcional)"
            )
            uploaded_files["palavras_chave"] = palavras_chave_file

        st.divider()
        st.subheader("Filtros de regra")

        enter_visitas_min = st.number_input("Entrar em Ads: visitas mín", min_value=0, value=50, step=10)
        enter_conv_min_pct = st.number_input(
            "Entrar em Ads: conversão mín (%)",
            min_value=0.0,
            value=3.0,
            step=0.5,
            format="%.2f",
        )
        pause_invest_min = st.number_input(
            "Pausar: investimento mín (R$)",
            min_value=0.0,
            value=20.0,
            step=10.0,
            format="%.2f",
        )
        pause_cvr_max_pct = st.number_input(
            "Pausar: CVR máx (%)",
            min_value=0.0,
            value=1.5,
            step=0.5,
            format="%.2f",
        )

        # IMPORTANTE: Conv_Visitas_Vendas e CVR chegam em pontos percentuais (ex.: 1,82 vira 1.82).
        enter_conv_min = enter_conv_min_pct
        pause_cvr_max = pause_cvr_max_pct


        st.divider()
        st.subheader("Regras por anúncio (Ads)")

        with st.expander("Ajustar regras de anúncio", expanded=False):
            st.caption("Impressões, cliques e investimento são filtros de volume. CTR e CVR são referências médias de e-commerce, ajuste conforme seu nicho.")
            ads_min_imp = st.number_input("Ads: impressões mín", min_value=0, value=500, step=100)
            ads_min_clk = st.number_input("Ads: cliques mín", min_value=0, value=10, step=5)
            ads_ctr_min_abs = st.number_input("Ads: CTR mín (%)  , referência 0,60%", min_value=0.0, value=0.60, step=0.05, format="%.2f")
            ads_cvr_min = st.number_input("Ads: CVR mín (%)  , referência 1,00%", min_value=0.0, value=1.00, step=0.10, format="%.2f")
            ads_pause_invest_min = st.number_input("Ads: investimento mín p/ pausar (R$)", min_value=0.0, value=20.0, step=10.0, format="%.2f")

        # CTR e CVR acima são em pontos percentuais (ex.: 0,80 = 0.80%)
        st.divider()
        executar = st.button("Gerar relatório", use_container_width=True)
        
        # Checkbox para decidir se quer baixar o snapshot automaticamente (apenas Mercado Livre)
        if selected_marketplace == "mercado_livre":
            st.divider()
            baixar_snapshot_auto = st.checkbox("Baixar Snapshot V2 automaticamente", value=True)
        else:
            baixar_snapshot_auto = False

    # Validação de arquivos obrigatórios baseada no marketplace
    if selected_marketplace == "mercado_livre":
        if not (uploaded_files.get("vendas") and uploaded_files.get("patrocinados") and uploaded_files.get("campanha")):
            st.info("📄 Envie os 3 arquivos obrigatórios do Mercado Livre na barra lateral para gerar o relatório.")
            return
    elif selected_marketplace == "shopee":
        if not uploaded_files.get("dados_gerais"):
            st.info("📄 Envie o arquivo de Dados Gerais de Anúncios da Shopee na barra lateral para gerar o relatório.")
            return

    # Verificação de arquivos para Mercado Livre (já feita acima, mas mantendo compatibilidade se necessário)
    if selected_marketplace == "mercado_livre":
        if not (organico_file and patrocinados_file and campanhas_file):
            st.info("Envie os 3 arquivos na barra lateral para liberar o relatório.")
            return

    if not executar:
        st.warning("Quando estiver pronto, clique em Gerar relatório.")
        return

    try:
        # Processamento condicional baseado no marketplace
        if selected_marketplace == "mercado_livre":
            # Processa arquivos do Mercado Livre
            org = ml.load_organico(uploaded_files["vendas"])
            pat = ml.load_patrocinados(uploaded_files["patrocinados"])

            # Modo unico: consolidado
            camp_raw = ml.load_campanhas_consolidado(uploaded_files["campanha"])
            camp_agg = ml.build_campaign_agg(camp_raw, modo="consolidado")

            kpis, pause, enter, scale, acos, camp_strat, ads_panel, ads_pausar, ads_vencedores, ads_otim_fotos, ads_otim_keywords, ads_otim_oferta = ml.build_tables(
            org=org,
            camp_agg=camp_agg,
            pat=pat,
            enter_visitas_min=int(enter_visitas_min),
            enter_conv_min=float(enter_conv_min),
            pause_invest_min=float(pause_invest_min),
            pause_cvr_max=float(pause_cvr_max),
            ads_min_imp=int(ads_min_imp) if ('ads_min_imp' in locals()) else 500,
            ads_min_clk=int(ads_min_clk) if ('ads_min_clk' in locals()) else 10,
            ads_ctr_min_abs=float(ads_ctr_min_abs) if ('ads_ctr_min_abs' in locals()) else 0.10,
            ads_cvr_min=float(ads_cvr_min) if ('ads_cvr_min' in locals()) else 0.80,
                ads_pause_invest_min=float(ads_pause_invest_min) if ('ads_pause_invest_min' in locals()) else 20.0,
            )

            # -------------------------
            # Snapshot V2 - Carregamento e Comparação
            # -------------------------
            camp_snap, anuncio_snap, kpis_snap = ml.load_snapshot_v2(uploaded_files.get("snapshot"))
        
            camp_strat_comp = ml.compare_snapshots_campanha(camp_strat, camp_snap)
            ads_panel_comp = ml.compare_snapshots_anuncio(ads_panel, anuncio_snap)
            
        elif selected_marketplace == "shopee":
            # Processa arquivos da Shopee
            resultado_shopee = shopee.processar_relatorio_shopee(
                dados_gerais_file=uploaded_files["dados_gerais"],
                palavras_chave_file=uploaded_files.get("palavras_chave")
            )
            
            kpis = resultado_shopee["kpis"]
            df_shopee_geral = resultado_shopee["df_geral"]
            df_shopee_protecao = resultado_shopee["df_protecao"]
            df_shopee_conversoes = resultado_shopee["df_conversoes"]
            recomendacoes_shopee = resultado_shopee["recomendacoes"]
            df_shopee_keywords = resultado_shopee.get("df_keywords", None)
            
            # Variáveis de compatibilidade (para evitar erros no código existente)
            camp_strat_comp = df_shopee_protecao
            ads_panel_comp = df_shopee_conversoes
            camp_snap = None
            anuncio_snap = None
            
            # Variáveis do Mercado Livre que não existem na Shopee
            pause = pd.DataFrame()
            enter = pd.DataFrame()
            scale = pd.DataFrame()
            acos = pd.DataFrame()
            camp_strat = df_shopee_protecao
            ads_panel = df_shopee_conversoes
            ads_pausar = pd.DataFrame()
            ads_vencedores = pd.DataFrame()
            ads_otim_fotos = pd.DataFrame()
            ads_otim_keywords = pd.DataFrame()
            ads_otim_oferta = pd.DataFrame()

        # -------------------------
        # Snapshot V2 - Salvamento Automático (Mercado Livre)
        # -------------------------
        if selected_marketplace == "mercado_livre" and baixar_snapshot_auto:
            try:
                # Gera um nome de arquivo único
                filename = f"snapshot_ml_ads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                snapshot_path = os.path.join(os.getcwd(), filename)
                # Passamos os KPIs globais para garantir paridade total no comparativo futuro
                ml.save_snapshot_v2(camp_strat, ads_panel, snapshot_path, kpis_globais=kpis)
                
                # Para download automático no Streamlit, usamos o download_button 
                # mas ele precisa ser clicado pelo usuário. 
                # Como alternativa de "auto-download", exibimos ele com destaque no topo.
                st.sidebar.success(f"Snapshot V2 preparado!")
                st.sidebar.download_button(
                    label="📥 CLIQUE AQUI PARA BAIXAR SNAPSHOT",
                    data=open(snapshot_path, "rb").read(),
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    key="auto_download_btn"
                )
            except Exception as e:
                st.sidebar.error(f"Erro ao preparar Snapshot: {e}")




        # -------------------------
        # Estoque (opcional) - ajuste apenas para exibicao (Mercado Livre)
        # -------------------------
        if selected_marketplace == "mercado_livre":
            blocked_stock = pd.DataFrame()
        pause_disp, enter_disp, scale_disp, acos_disp = pause, enter, scale, acos
        camp_strat_disp = camp_strat_comp.copy()
        ads_panel_disp = ads_panel_comp.copy()
        if "usar_estoque" in locals() and usar_estoque and estoque_file is not None:
            try:
                stock_df = load_stock_file(estoque_file)
                pause_disp = enrich_with_stock(pause_disp, stock_df)
                enter_disp = enrich_with_stock(enter_disp, stock_df)
                scale_disp = enrich_with_stock(scale_disp, stock_df)
                acos_disp  = enrich_with_stock(acos_disp, stock_df)
                enter_disp, scale_disp, acos_disp, pause_disp, blocked_stock = apply_stock_rules(
                    enter_disp, scale_disp, acos_disp, pause_disp,
                    estoque_min_ads=int(estoque_min_ads),
                    estoque_baixo=int(estoque_baixo),
                    estoque_critico=int(estoque_critico),
                    tratar_estoque_vazio_como_zero=bool(tratar_estoque_vazio_como_zero),
                )
            except Exception as e:
                st.warning(f"Não consegui aplicar a visão de estoque: {e}")

    except Exception as e:
        st.error("Erro ao processar os arquivos.")
        st.exception(e)
        return

    # -------------------------
    # Sumário Executivo (Minimalista)
    # -------------------------
    st.header("Resumo Executivo")
    
    # Geração do texto do sumário
    def generate_executive_summary(kpis, camp_strat_comp, ads_panel_comp):
        # Tenta pegar ROAS (ML) ou ROAS Médio (Shopee)
        roas_val = float(kpis.get("ROAS", kpis.get("ROAS Médio", 0)))
        
        # Análise de Quadrantes (Protegida contra colunas ausentes)
        q_hemorragia = 0
        q_escala = 0
        if "Quadrante" in camp_strat_comp.columns:
            q_counts = camp_strat_comp["Quadrante"].value_counts()
            q_hemorragia = q_counts.get("HEMORRAGIA", 0)
            q_escala = q_counts.get("ESCALA_ORCAMENTO", 0)
        elif selected_marketplace == "shopee" and "Status Proteção" in camp_strat_comp.columns:
            # Mapeamento simples para Shopee para preencher os cards do sumário
            q_counts = camp_strat_comp["Status Proteção"].value_counts()
            q_hemorragia = q_counts.get("🛡️ Elegível", 0) + q_counts.get("⚠️ Atenção", 0)
            # Para escala na Shopee, poderíamos olhar as recomendações, mas por ora mantemos 0 ou lógica simples
            if "ROAS" in camp_strat_comp.columns:
                q_escala = camp_strat_comp[camp_strat_comp["ROAS"] >= 4.0].shape[0]
        
        # Análise de Migração (Protegida contra colunas ausentes)
        migracao_melhora = 0
        migracao_piora = 0
        if "Migracao_Quadrante" in camp_strat_comp.columns:
            migracao_melhora = camp_strat_comp[camp_strat_comp["Migracao_Quadrante"].str.contains("HEMORRAGIA PARA ESTÁVEL|HEMORRAGIA PARA ESCALA|ESTÁVEL PARA ESCALA", na=False)].shape[0]
            migracao_piora = camp_strat_comp[camp_strat_comp["Migracao_Quadrante"].str.contains("ESTÁVEL PARA HEMORRAGIA|ESCALA PARA HEMORRAGIA", na=False)].shape[0]
        
        # Análise de Anúncios
        ads_pausar = ads_panel_comp[ads_panel_comp["Acao_Anuncio"] == "Pausar anúncio"].shape[0] if "Acao_Anuncio" in ads_panel_comp.columns else 0
        
        # 1. Status Geral (Badge Colorido)
        if q_hemorragia > 0 and roas_val < 4.0:
            st.error("⊘ STATUS CRÍTICO: Hemorragia alta e ROAS abaixo da meta.")
        elif q_escala > 0:
            st.info("⚡ STATUS ATENÇÃO: Oportunidades de escala não aproveitadas.")
        else:
            st.success("◈ STATUS SAUDÁVEL: Conta controlada e ROAS acima da meta.")
            
        st.divider()
        
        # 2. Cards de Insights Rápidos (Grid 1x3)
        col1, col2, col3 = st.columns(3)
        
        col1.metric("⚡ Escala", f"{q_escala} Campanhas", "Aumentar Orçamento")
        col2.metric("⊘ Hemorragia", f"{q_hemorragia} Campanhas", "Pausar ou Otimizar")
        col3.metric("✕ Pausar", f"{ads_pausar} Anúncios", "Baixo Desempenho")
        
        st.divider()
        
        # 3. Plano de Ação "Direto ao Ponto"
        st.subheader("Plano de Ação Imediato")
        
        # Ações Urgentes (Hemorragia)
        if q_hemorragia > 0:
            st.markdown(f"- **Estancar Hemorragia**: {q_hemorragia} campanhas exigem ação imediata (pausar ou reduzir ROAS objetivo).")
        
        # Ações de Escala
        if q_escala > 0:
            st.markdown(f"- **Destravar Escala**: {q_escala} campanhas estão prontas para aumento de orçamento.")
            
        # Ações de Migração (se houver snapshot)
        if migracao_melhora > 0 or migracao_piora > 0:
            st.subheader("Evolução da Estratégia (vs. Snapshot)")
            if migracao_melhora > 0:
                st.markdown(f"- **{migracao_melhora} Campanhas Melhoraram** de quadrante (sucesso nas ações passadas).")
            if migracao_piora > 0:
                st.markdown(f"- **{migracao_piora} Campanhas Pioraram** de quadrante (revisar ações ou fatores externos).")
        
        # Retorna uma string vazia, pois a função agora desenha a interface diretamente
        return ""

    # A função agora desenha a interface diretamente, então apenas a chamamos
    generate_executive_summary(kpis, camp_strat_comp, ads_panel_comp)
    
    st.divider()
    
    # -------------------------
    # KPIs
    # -------------------------
    st.header("Indicadores Chave de Performance (KPIs)")
    
    if selected_marketplace == "mercado_livre":
        cols = st.columns(4)

        invest_ads = float(kpis.get("Investimento Ads (R$)", 0))
        receita_ads = float(kpis.get("Receita Ads (R$)", 0))
        roas_val = float(kpis.get("ROAS", 0))
        tacos_val = float(kpis.get("TACOS", 0))
        tacos_pct = tacos_val * 100 if tacos_val <= 2 else tacos_val

        cols[0].metric("⟀ Investimento", fmt_money_br(invest_ads))
        cols[1].metric("⟁ Receita", fmt_money_br(receita_ads))
        
        # ROAS com cor dinâmica
        roas_label = "Bom" if roas_val >= 5 else "Abaixo da meta"
        cols[2].metric(
            "◎ ROAS", 
            fmt_number_br(roas_val, 2), 
            delta=roas_label, 
            delta_color="normal" if roas_val >= 5 else "inverse"
        )

        # TACOS com cor dinâmica
        if tacos_pct <= 3:
            tacos_label = "Excelente"
            tacos_color = "normal"
        elif tacos_pct <= 5:
            tacos_label = "Bom"
            tacos_color = "normal"
        elif tacos_pct <= 7:
            tacos_label = "Alto"
            tacos_color = "inverse"
        else:
            tacos_label = "Muito Alto"
            tacos_color = "inverse"
        
        cols[3].metric("⊞ TACOS", fmt_percent_br(tacos_pct), delta=tacos_label, delta_color=tacos_color)

    elif selected_marketplace == "shopee":
        gmv_total = float(kpis.get("GMV Total", 0))
        despesas = float(kpis.get("Despesas", 0))
        roas_medio = float(kpis.get("ROAS Médio", 0))
        roas_direto = float(kpis.get("ROAS Direto Médio", 0))
        credito_protecao = float(kpis.get("Crédito Proteção Total", 0))
        campanhas_protegidas = int(kpis.get("Campanhas com Proteção", 0))
        
        # Renderiza KPIs da Shopee
        lgc.render_glass_kpi_row([
            {
                "icon": "💰",
                "label": "GMV TOTAL",
                "value": fmt_money_br(gmv_total)
            },
            {
                "icon": "💵",
                "label": "DESPESAS",
                "value": fmt_money_br(despesas)
            },
            {
                "icon": "📈",
                "label": "ROAS MÉDIO",
                "value": f"{fmt_number_br(roas_medio, 2)}x"
            },
            {
                "icon": "🎯",
                "label": "ROAS DIRETO",
                "value": f"{fmt_number_br(roas_direto, 2)}x"
            },
            {
                "icon": "🛡️",
                "label": "CRÉDITO PROTEÇÃO",
                "value": fmt_money_br(credito_protecao)
            },
            {
                "icon": "✅",
                "label": "CAMPANHAS PROTEGIDAS",
                "value": str(campanhas_protegidas)
            }
        ])
        
        # Funil de Vendas (Shopee)
        st.markdown("---")
        impressoes_shopee = int(df_shopee_protecao["Impressões"].sum()) if "Impressões" in df_shopee_protecao.columns else 0
        cliques_shopee = int(df_shopee_protecao["Cliques"].sum()) if "Cliques" in df_shopee_protecao.columns else 0
        vendas_shopee = int(df_shopee_protecao["Itens Vendidos"].sum()) if "Itens Vendidos" in df_shopee_protecao.columns else 0
        
        funil_html_shopee = sf.create_sales_funnel_html(impressoes_shopee, cliques_shopee, vendas_shopee)
        st.components.v1.html(funil_html_shopee, height=480, scrolling=False)
    
    st.divider()

    # -------------------------
    # Gráficos de Análise (Mercado Livre)
    # -------------------------
    if selected_marketplace == "mercado_livre":
        st.header("Análise Visual de Performance")
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            render_pareto_chart(camp_strat)
        
        with col_g2:
            render_treemap_chart(camp_strat)

        st.divider()
    
    # -------------------------
    # Análise Shopee - Proteção de ROAS e Conversões
    # -------------------------
    elif selected_marketplace == "shopee":
        st.header("🛡️ Análise de Proteção de ROAS")
        
        # Estatísticas de Proteção
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Campanhas Elegíveis",
                campanhas_protegidas,
                help="Campanhas com taxa de cumprimento de ROAS < 90%"
            )
        
        with col2:
            taxa_media = df_shopee_protecao['Taxa Cumprimento ROAS (%)'].mean()
            st.metric(
                "Taxa Média Cumprimento",
                f"{taxa_media:.1f}%",
                help="Taxa média de cumprimento de ROAS de todas as campanhas"
            )
        
        with col3:
            conversoes_totais = int(kpis.get("Conversões", 0))
            st.metric(
                "Conversões Totais",
                conversoes_totais
            )
        
        with col4:
            conversoes_diretas = int(kpis.get("Conversões Diretas", 0))
            pct_diretas = (conversoes_diretas / conversoes_totais * 100) if conversoes_totais > 0 else 0
            st.metric(
                "Conversões Diretas",
                conversoes_diretas,
                delta=f"{pct_diretas:.1f}% do total"
            )
        
        st.divider()
        
        # Tabela de Campanhas com Proteção
        with st.expander("🛡️ Campanhas Elegíveis para Proteção de ROAS", expanded=True):
            df_elegiveis = df_shopee_protecao[df_shopee_protecao['Elegível Proteção']].copy()
            
            if len(df_elegiveis) > 0:
                # Seleciona colunas relevantes
                colunas_exibir = [
                    'Nome do Anúncio', 'Status', 'GMV', 'Despesas', 'ROAS',
                    'ROAS Alvo', 'Taxa Cumprimento ROAS (%)', 'Crédito Potencial (R$)',
                    'Status Proteção'
                ]
                colunas_disponiveis = [col for col in colunas_exibir if col in df_elegiveis.columns]
                
                st.dataframe(
                    df_elegiveis[colunas_disponiveis],
                    use_container_width=True,
                    hide_index=True
                )
                
                st.info(f"📊 Total de crédito potencial: **{fmt_money_br(credito_protecao)}**")
            else:
                st.success("✅ Nenhuma campanha elegível para proteção. Todas estão com ROAS acima de 90% da meta!")
        
        st.divider()
        
        # Análise de Conversões Diretas
        with st.expander("🎯 Análise de Conversões Diretas vs Totais", expanded=False):
            colunas_conversoes = [
                'Nome do Anúncio', 'Conversões', 'Conversões Diretas',
                '% Conversões Diretas', 'Qualidade Atribuição',
                'GMV', 'Receita direta', 'ROAS', 'ROAS Direto'
            ]
            colunas_conv_disponiveis = [col for col in colunas_conversoes if col in df_shopee_conversoes.columns]
            
            st.dataframe(
                df_shopee_conversoes[colunas_conv_disponiveis],
                use_container_width=True,
                hide_index=True
            )
        
        st.divider()
        
        # Recomendações
        st.header("💡 Recomendações Estratégicas")
        
        tab1, tab2, tab3, tab4 = st.tabs([
            "🛡️ Ativar Proteção",
            "🔧 Otimizar ROAS",
            "🚀 Escalar GMV",
            "⚠️ Pausar/Revisar"
        ])
        
        with tab1:
            if len(recomendacoes_shopee["ativar_protecao"]) > 0:
                st.subheader("Campanhas para Ativar Proteção de ROAS")
                for rec in recomendacoes_shopee["ativar_protecao"]:
                    st.markdown(f'''
                    **{rec['campanha']}**
                    - ROAS Atual: {rec['roas_atual']:.2f}x
                    - Despesas: {fmt_money_br(rec['despesas'])}
                    - Motivo: {rec['motivo']}
                    ''')
                    st.divider()
            else:
                st.info("✅ Nenhuma campanha precisa ativar proteção no momento.")
        
        with tab2:
            if len(recomendacoes_shopee["otimizar_roas"]) > 0:
                st.subheader("Campanhas para Otimizar ROAS")
                for rec in recomendacoes_shopee["otimizar_roas"]:
                    st.markdown(f'''
                    **{rec['campanha']}**
                    - ROAS Atual: {rec['roas_atual']:.2f}x
                    - Conversões: {rec['conversoes']}
                    - Motivo: {rec['motivo']}
                    ''')
                    st.divider()
            else:
                st.info("✅ Nenhuma campanha precisa de otimização urgente.")
        
        with tab3:
            if len(recomendacoes_shopee["escalar_gmv"]) > 0:
                st.subheader("Oportunidades de Escalar GMV")
                for rec in recomendacoes_shopee["escalar_gmv"]:
                    st.markdown(f'''
                    **{rec['campanha']}**
                    - ROAS Atual: {rec['roas_atual']:.2f}x
                    - GMV: {fmt_money_br(rec['gmv'])}
                    - Motivo: {rec['motivo']}
                    ''')
                    st.divider()
            else:
                st.info("🔍 Nenhuma oportunidade de escala identificada no momento.")
        
        with tab4:
            if len(recomendacoes_shopee["pausar_revisar"]) > 0:
                st.subheader("⚠️ Campanhas para Pausar ou Revisar")
                for rec in recomendacoes_shopee["pausar_revisar"]:
                    st.markdown(f'''
                    **{rec['campanha']}**
                    - ROAS Atual: {rec['roas_atual']:.2f}x
                    - Despesas: {fmt_money_br(rec['despesas'])}
                    - Conversões: {rec['conversoes']}
                    - Motivo: {rec['motivo']}
                    ''')
                    st.divider()
            else:
                st.success("✅ Nenhuma campanha precisa ser pausada.")
        
        st.divider()

    # -------------------------
    # Painel geral (Mercado Livre)
    # -------------------------
    if selected_marketplace == "mercado_livre":
        with st.expander("Painel Geral de Campanhas", expanded=True):
            panel_raw = ml.build_control_panel(camp_strat)
            panel_raw = replace_acos_obj_with_roas_obj(panel_raw)
            panel_view = prepare_df_for_view(panel_raw, drop_cpi_cols=True, drop_roas_generic=False)
            st.dataframe(format_table_br(panel_view), use_container_width=True)

        # Funil de Vendas abaixo do painel para maior destaque
        st.divider()
        render_funnel_chart(kpis)
        st.divider()

        # -------------------------
        # Matriz CPI
        # -------------------------
        with st.expander("Matriz CPI (Oportunidades de Otimização)", expanded=False):
            cpi_raw = replace_acos_obj_with_roas_obj(camp_strat)
            # Visao limpa (sem alterar calculos): esconder colunas auxiliares, remover duplicidades e alinhar ROAS/ACOS
            cpi_view = prepare_df_for_view(cpi_raw, drop_cpi_cols=True, drop_roas_generic=True)
            st.dataframe(format_table_br(cpi_view), use_container_width=True)

        st.divider()
    with st.expander("Análise Tática por Anúncio", expanded=False):
        if ads_panel is None or (hasattr(ads_panel, "empty") and ads_panel.empty):
            st.info("Sem dados de anúncios patrocinados para analisar.")
        else:
            # KPIs rápidos do bloco
            total_ads = int(len(ads_panel))
            n_pausar = int(len(ads_pausar)) if ads_pausar is not None else 0
            n_vencedores = int(len(ads_vencedores)) if ads_vencedores is not None else 0
            n_fotos = int(len(ads_otim_fotos)) if ads_otim_fotos is not None else 0
            n_kw = int(len(ads_otim_keywords)) if ads_otim_keywords is not None else 0
            n_oferta = int(len(ads_otim_oferta)) if ads_otim_oferta is not None else 0

            c1, c2, c3, c4, c5, c6 = st.columns(6)
            c1.metric("Total Anúncios", total_ads)
            c2.metric("◈ Vencedores", n_vencedores)
            c3.metric("✕ Pausar", n_pausar)
            c4.metric("◨ Fotos/Clips", n_fotos)
            c5.metric("⌨ Keywords", n_kw)
            c6.metric("🏷 Oferta", n_oferta)

            st.divider()

            tab_pausar, tab_vencedores, tab_otim, tab_completo = st.tabs([
                "✕ Pausar", "◈ Vencedores", "🔧 Otimização", "📊 Painel"
            ])

            with tab_pausar:
                st.subheader("Anúncios para pausar (refino de campanha)")
                ads_pausar_view = prepare_df_for_view(ads_pausar, drop_cpi_cols=True, drop_roas_generic=False) if ads_pausar is not None else pd.DataFrame()
                st.dataframe(format_table_br(ads_pausar_view), use_container_width=True)

            with tab_vencedores:
                st.subheader("Anúncios vencedores (preservar)")
                ads_vencedores_view = prepare_df_for_view(ads_vencedores, drop_cpi_cols=True, drop_roas_generic=False) if ads_vencedores is not None else pd.DataFrame()
                st.dataframe(format_table_br(ads_vencedores_view), use_container_width=True)

            with tab_otim:
                st.subheader("Anúncios para otimização")
                t1, t2, t3 = st.tabs(["📸 Fotos e Clips", "⌨️ Palavras-chave", "🏷️ Oferta"])
                with t1:
                    v = prepare_df_for_view(ads_otim_fotos, drop_cpi_cols=True, drop_roas_generic=False) if ads_otim_fotos is not None else pd.DataFrame()
                    st.dataframe(format_table_br(v), use_container_width=True)
                with t2:
                    v = prepare_df_for_view(ads_otim_keywords, drop_cpi_cols=True, drop_roas_generic=False) if ads_otim_keywords is not None else pd.DataFrame()
                    st.dataframe(format_table_br(v), use_container_width=True)
                with t3:
                    v = prepare_df_for_view(ads_otim_oferta, drop_cpi_cols=True, drop_roas_generic=False) if ads_otim_oferta is not None else pd.DataFrame()
                    st.dataframe(format_table_br(v), use_container_width=True)

            with tab_completo:
                st.subheader("Painel completo por anúncio")
                ads_view = prepare_df_for_view(ads_panel, drop_cpi_cols=True, drop_roas_generic=False)
                st.dataframe(format_table_br(ads_view), use_container_width=True)

    # -------------------------
    # Plano de Ação 15 Dias
    # -------------------------
    st.header("Plano de Ação Estratégico (15 Dias)")
    
    if selected_marketplace == "mercado_livre":
        st.info("Este plano respeita a janela de 7 dias do algoritmo do Mercado Livre. Não faça alterações nas mesmas campanhas em intervalos menores que uma semana.")
        plan15 = ml.build_15_day_plan(camp_strat)
    else:
        # Para Shopee, por enquanto não temos um plano de 15 dias estruturado da mesma forma
        # mas podemos exibir as recomendações geradas
        st.info("Plano de ação baseado nas recomendações de performance da Shopee.")
        plan15 = pd.DataFrame() # Ou lógica futura para Shopee
    
    if not plan15.empty:
        # Estilização básica para o plano
        def color_fase(val):
            if "Semana 1" in str(val): return "color: #3483fa; font-weight: bold"
            if "Semana 2" in str(val): return "color: #ffe600; font-weight: bold"
            return ""
        
        st.dataframe(
            plan15.style.applymap(color_fase, subset=["Fase"]),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.write("Nenhuma ação necessária para o período atual.")

    st.divider()

    # -------------------------
    # Restante do dashboard (com os mesmos ajustes)
    # -------------------------
    pause_view = prepare_df_for_view(replace_acos_obj_with_roas_obj(pause_disp), drop_cpi_cols=True, drop_roas_generic=False)
    pause_fmt = format_table_br(pause_view)
    enter_view = prepare_df_for_view(replace_acos_obj_with_roas_obj(enter_disp), drop_cpi_cols=True, drop_roas_generic=False)
    enter_fmt = format_table_br(enter_view)
    scale_view = prepare_df_for_view(replace_acos_obj_with_roas_obj(scale_disp), drop_cpi_cols=True, drop_roas_generic=False)
    scale_fmt = format_table_br(scale_view)
    acos_view = prepare_df_for_view(replace_acos_obj_with_roas_obj(acos_disp), drop_cpi_cols=True, drop_roas_generic=False)
    acos_fmt = format_table_br(acos_view)

    st.header("Ações Recomendadas por Categoria")
    
    tab_pausar, tab_entrar, tab_escalar, tab_roas = st.tabs([
        "✕ Pausar", "✓ Entrar", "⚡ Escalar", "◎ ROAS Obj"
    ])

    with tab_pausar:
        st.subheader("Campanhas para pausar ou revisar")
        st.info("Campanhas com ROAS baixo ou investimento sem retorno.")
        st.dataframe(pause_fmt, use_container_width=True)
    
    with tab_entrar:
        st.subheader("Oportunidades para entrar em Ads")
        st.info("Anúncios orgânicos com alta conversão que ainda não estão em Ads.")
        st.dataframe(enter_fmt, use_container_width=True)

    with tab_escalar:
        st.subheader("Campanhas para escalar orçamento")
        st.info("Campanhas com ROAS forte que estão perdendo impressões por orçamento.")
        st.dataframe(scale_fmt, use_container_width=True)

    with tab_roas:
        st.subheader("Campanhas para baixar ROAS objetivo")
        st.info("Campanhas competitivas que podem ganhar mais mercado reduzindo o ROAS alvo.")
        st.dataframe(acos_fmt, use_container_width=True)

    # -------------------------
    # Visão de Estoque (opcional)
    # -------------------------
    if "usar_estoque" in locals() and usar_estoque and estoque_file is not None:
        with st.expander("📦 Visão de Estoque", expanded=False):
            if not blocked_stock.empty:
                st.subheader("Bloqueados por estoque (iriam para Ads, mas não têm quantidade mínima)")
                st.dataframe(format_table_br(prepare_df_for_view(replace_acos_obj_with_roas_obj(blocked_stock), drop_cpi_cols=True, drop_roas_generic=False)), use_container_width=True)
            else:
                st.write("Nenhum item foi bloqueado por estoque nas regras atuais.")

            # Risco de ruptura dentro das ações
            risco = pd.concat([pause_disp, scale_disp, acos_disp], ignore_index=True)
            if "Estoque_Status" in risco.columns:
                risco = risco[risco["Estoque_Status"].isin(["ZERADO", "CRITICO", "BAIXO"])].copy()
            if not risco.empty:
                st.subheader("Risco de ruptura nas ações")
                risco_view = prepare_df_for_view(replace_acos_obj_with_roas_obj(risco), drop_cpi_cols=True, drop_roas_generic=False)
                st.dataframe(format_table_br(risco_view), use_container_width=True)
            else:
                st.write("Sem alertas de estoque nas ações atuais.")

    # -------------------------
    # Funcionalidades "Engine" - Smart Budget, Motor Aquecido, Filtro de Combustível
    # -------------------------
    if selected_marketplace == "mercado_livre" and camp_strat is not None and not camp_strat.empty:
        try:
            from engine_integration import render_engine_features
            render_engine_features(
                camp_strat=camp_strat,
                stock_df=stock_df if "stock_df" in locals() else None,
                usar_estoque=usar_estoque if "usar_estoque" in locals() else False,
                fmt_money_br_func=fmt_money_br,
                fmt_int_br_func=fmt_int_br
            )
        except Exception as e:
            st.warning(f"⚠️ Erro ao carregar funcionalidades Engine: {str(e)}")
    
    st.divider()
    
    # -------------------------
    # Download Excel
    # Mantem dataframes originais para nao quebrar o gerar_excel do ml_report
    # -------------------------
    st.header("Download do Relatório Completo")
    
    if selected_marketplace == "mercado_livre":
        try:
            excel_bytes = ml.gerar_excel(
                kpis=kpis,
                camp_agg=camp_agg,
                pause=pause,
                enter=enter,
                scale=scale,
                acos=acos,
                camp_strat=camp_strat,
                ads_panel=ads_panel,
                camp_strat_comp=camp_strat_comp,
                daily=None,
            )

            st.download_button(
                "Baixar Excel do relatório",
                data=excel_bytes,
                file_name="relatorio_meli_ads.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        except Exception as e:
            st.error("Não consegui gerar o Excel.")
            st.exception(e)
    else:
        # Para Shopee, geramos um Excel simplificado com os dados processados
        try:
            from io import BytesIO
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                # Aba de KPIs
                kpis_df = pd.DataFrame([kpis])
                kpis_df.to_excel(writer, sheet_name='KPIs_Gerais', index=False)
                
                # Aba de Dados Gerais
                if 'df_shopee_geral' in locals():
                    df_shopee_geral.to_excel(writer, sheet_name='Dados_Gerais', index=False)
                
                # Aba de Proteção de ROAS
                if 'df_shopee_protecao' in locals():
                    df_shopee_protecao.to_excel(writer, sheet_name='Protecao_ROAS', index=False)
                
                # Aba de Conversões
                if 'df_shopee_conversoes' in locals():
                    df_shopee_conversoes.to_excel(writer, sheet_name='Analise_Conversoes', index=False)
                
                # Aba de Palavras-chave
                if 'df_shopee_keywords' in locals() and df_shopee_keywords is not None:
                    df_shopee_keywords.to_excel(writer, sheet_name='Palavras_Chave', index=False)
            
            excel_data = output.getvalue()
            st.download_button(
                "Baixar Excel do relatório Shopee",
                data=excel_data,
                file_name="relatorio_shopee_ads.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        except Exception as e:
            st.error("Não consegui gerar o Excel da Shopee.")
            st.exception(e)


    st.divider()
    
    # -------------------------
    # Seção Dedicada: Evolução e Resultados (Comparativo)
    # -------------------------
    if camp_snap is not None and not camp_snap.empty:
        st.divider()
        st.header("Evolução e Resultados (Comparativo)")
        st.success("Snapshot de referência detectado. Analisando evolução das campanhas e anúncios.")
        
        # KPIs Comparativos Globais
        st.subheader("Resumo de Performance (Antes vs. Depois)")
        
        # Priorizamos os KPIs globais salvos no snapshot para garantir paridade total
        if kpis_snap and isinstance(kpis_snap, dict) and "Investimento Ads (R$)" in kpis_snap:
            snap_invest = float(kpis_snap.get("Investimento Ads (R$)", 0))
            snap_receita = float(kpis_snap.get("Receita Ads (R$)", 0))
            snap_roas = float(kpis_snap.get("ROAS", 0))
            pass
        else:
            # Fallback para snapshots antigos (soma das campanhas ativas)
            snap_invest = float(pd.to_numeric(camp_snap["Investimento"], errors="coerce").fillna(0).sum())
            snap_receita = float(pd.to_numeric(camp_snap["Receita"], errors="coerce").fillna(0).sum())
            snap_roas = snap_receita / snap_invest if snap_invest > 0 else 0
        
        delta_invest = invest_ads - snap_invest
        delta_receita = receita_ads - snap_receita
        delta_roas = roas_val - snap_roas
        
        # Formatação de deltas para evitar "R$ -0,00" ou "0,00x" quando idênticos
        # Aumentamos a tolerância para R$ 1,00 para evitar ruídos de arredondamento de centavos em grandes volumes
        def fmt_delta_money(val):
            if val is None or abs(val) < 1.0: return None
            return fmt_money_br(val)
            
        def fmt_delta_roas(val):
            if val is None or abs(val) < 0.01: return None
            return f"{val:+.2f}x"

        c_cols = st.columns(4)
        c_cols[0].metric("⟀ Investimento", fmt_money_br(invest_ads), delta=fmt_delta_money(delta_invest), delta_color="inverse")
        c_cols[1].metric("⟁ Receita", fmt_money_br(receita_ads), delta=fmt_delta_money(delta_receita))
        c_cols[2].metric("◎ ROAS", f"{roas_val:.2f}x", delta=fmt_delta_roas(delta_roas))
        
        # Tacos Delta (se disponível)
        c_cols[3].metric("⊞ TACOS", fmt_percent_br(tacos_pct), delta="Atual")

        st.divider()
        
        tab_ev_camp, tab_ev_ads = st.tabs(["Evolução de Campanhas", "Evolução de Anúncios (MLB)"])
        
        with tab_ev_camp:
            st.subheader("Migração de Quadrantes")
            migracao_counts = camp_strat_disp["Migracao_Quadrante"].value_counts().reset_index()
            migracao_counts.columns = ["Migração", "Contagem"]
            st.dataframe(migracao_counts, use_container_width=True)

            st.subheader("Tabela Comparativa de Campanhas")
            cols_to_show = [
                "Nome", "Quadrante", "Migracao_Quadrante", "Acao_Recomendada", 
                "Investimento", "Delta_Investimento", "Receita", "Delta_Receita", 
                "ROAS_Real", "Delta_ROAS", "ROAS_Real_Snap", "Acao_Recomendada_Snap"
            ]
            camp_comp_view = prepare_df_for_view(camp_strat_disp[[c for c in cols_to_show if c in camp_strat_disp.columns]], drop_cpi_cols=True, drop_roas_generic=False)
            st.dataframe(format_table_br(camp_comp_view), use_container_width=True)

        with tab_ev_ads:
            if anuncio_snap is not None and not anuncio_snap.empty:
                st.subheader("Migração de Status de Anúncios")
                migracao_counts_ads = ads_panel_disp["Migracao_Status"].value_counts().reset_index()
                migracao_counts_ads.columns = ["Migração", "Contagem"]
                st.dataframe(migracao_counts_ads, use_container_width=True)

                st.subheader("Tabela Comparativa de Anúncios (MLB)")
                cols_to_show_ads = [
                    "ID", "Titulo", "Campanha", "Status_Anuncio", "Migracao_Status", 
                    "Investimento", "Delta_Investimento", "Receita", "Delta_Receita", 
                    "ROAS_Real", "Delta_ROAS", "ROAS_Real_Snap", "Acao_Anuncio", "Acao_Anuncio_Snap"
                ]
                ads_comp_view = prepare_df_for_view(ads_panel_disp[[c for c in cols_to_show_ads if c in ads_panel_disp.columns]], drop_cpi_cols=True, drop_roas_generic=False)
                st.dataframe(format_table_br(ads_comp_view), use_container_width=True)
            else:
                st.info("O snapshot carregado não contém dados detalhados de anúncios para comparação.")

    # -------------------------
    # Rodapé
    # -------------------------
    st.divider()
    st.markdown(
        """
        <div style='text-align: center; color: #888888; padding: 20px;'>
            © Desenvolvido por Vinicius Lima / CNPJ: 47.192.694/0001-70
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
