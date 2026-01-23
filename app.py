import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import re

import ml_report as ml
import os


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
    if df is None or df.empty or stock_df is None or stock_df.empty:
        return df
    
    df = df.copy()
    
    # Normaliza chaves em ambos os DFs
    df["MLB_key"] = df.get("MLB", "").astype(str).str.strip()
    df["SKU_key"] = df.get("SKU", "").astype(str).str.strip().str.upper()
    
    # Merge por MLB (left join)
    df = df.merge(stock_df[["MLB_key", "Estoque"]], on="MLB_key", how="left")
    
    # Onde MLB não achou, tenta SKU
    mask_na = df["Estoque"].isna()
    if mask_na.any():
        df_sku = df[mask_na].merge(stock_df[["SKU_key", "Estoque"]], on="SKU_key", how="left")
        df.loc[mask_na, "Estoque"] = df_sku["Estoque"]
    
    # Preenche NaN com 0
    df["Estoque"] = df["Estoque"].fillna(0).astype(int)
    
    return df

def apply_stock_rules(enter_df, scale_df, acos_df, pause_df,
                      estoque_min_ads=6, estoque_baixo=6, estoque_critico=3,
                      tratar_estoque_vazio_como_zero=False) -> tuple:
    """
    Aplica regras de estoque:
    - Estoque crítico (<3): Pausar
    - Estoque baixo (3-6): Pausar se estiver em ACOS
    - Estoque mínimo (6+): Liberar
    """
    blocked = pd.DataFrame()
    
    for df_list in [enter_df, scale_df, acos_df, pause_df]:
        if df_list is not None and not df_list.empty and "Estoque" in df_list.columns:
            # Crítico: pausar
            critico = df_list[df_list["Estoque"] < estoque_critico].copy()
            if not critico.empty:
                critico["Motivo_Bloqueio"] = "Estoque crítico"
                blocked = pd.concat([blocked, critico], ignore_index=True)
            
            # Baixo em ACOS: pausar
            if df_list is acos_df:
                baixo = df_list[(df_list["Estoque"] >= estoque_critico) & (df_list["Estoque"] < estoque_baixo)].copy()
                if not baixo.empty:
                    baixo["Motivo_Bloqueio"] = "Estoque baixo em ACOS"
                    blocked = pd.concat([blocked, baixo], ignore_index=True)
    
    return enter_df, scale_df, acos_df, pause_df, blocked

def replace_acos_obj_with_roas_obj(df):
    """
    Substitui colunas de ACOS (que são objetos) por ROAS equivalente.
    Mantém a estrutura de dados intacta.
    """
    if df is None or df.empty:
        return df
    
    df = df.copy()
    
    # Se ACOS_Real é objeto, converte para numérico
    if "ACOS_Real" in df.columns and df["ACOS_Real"].dtype == object:
        df["ACOS_Real"] = pd.to_numeric(df["ACOS_Real"], errors="coerce").fillna(0)
    
    # Se ROAS_Real é objeto, converte para numérico
    if "ROAS_Real" in df.columns and df["ROAS_Real"].dtype == object:
        df["ROAS_Real"] = pd.to_numeric(df["ROAS_Real"], errors="coerce").fillna(0)
    
    return df

def prepare_df_for_view(df, drop_cpi_cols=True, drop_roas_generic=False):
    """
    Prepara DataFrame para exibição:
    - Remove colunas auxiliares
    - Renomeia para português
    - Ordena por importância
    """
    if df is None or df.empty:
        return df
    
    df = df.copy()
    
    # Colunas a remover
    cols_to_drop = []
    if drop_cpi_cols:
        cols_to_drop += ["MLB_key", "SKU_key", "Estoque"]
    if drop_roas_generic:
        cols_to_drop += ["ROAS", "ACOS"]
    
    for col in cols_to_drop:
        if col in df.columns:
            df = df.drop(columns=[col])
    
    # Reordena colunas importantes
    priority_cols = ["Nome", "Investimento", "Receita", "Qtd_Vendas", "ROAS_Real", "ACOS_Real", "Quadrante"]
    existing_priority = [c for c in priority_cols if c in df.columns]
    other_cols = [c for c in df.columns if c not in existing_priority]
    
    return df[existing_priority + other_cols]

def format_table_br(df):
    """
    Formata tabela para exibição em português.
    """
    if df is None or df.empty:
        return df
    
    df = df.copy()
    
    # Formata colunas numéricas
    for col in df.columns:
        if "Investimento" in col or "Receita" in col:
            df[col] = df[col].apply(lambda x: fmt_money_br(x) if pd.notna(x) else "")
        elif "ROAS" in col or "ACOS" in col:
            df[col] = df[col].apply(lambda x: fmt_number_br(x, 2) if pd.notna(x) else "")
        elif "Qtd" in col or "Cliques" in col or "Impressões" in col:
            df[col] = df[col].apply(lambda x: fmt_int_br(x) if pd.notna(x) else "")
    
    return df

def render_pareto_chart(df):
    """Gera um gráfico de Pareto mostrando Receita e % Acumulado por Campanha."""
    if df is None or df.empty or "Receita" not in df.columns:
        return
    
    df_sorted = df.sort_values("Receita", ascending=False).copy()
    df_sorted["Receita_Cum_Pct"] = 100 * df_sorted["Receita"].cumsum() / df_sorted["Receita"].sum()
    
    fig = go.Figure()
    
    # Barras de Receita (verde militar)
    fig.add_trace(go.Bar(
        x=df_sorted["Nome"],
        y=df_sorted["Receita"],
        name="Receita",
        marker_color="#556B2F"
    ))
    
    # Linha de Percentual Acumulado (verde militar claro)
    fig.add_trace(go.Scatter(
        x=df_sorted["Nome"],
        y=df_sorted["Receita_Cum_Pct"],
        name="% Acumulado",
        yaxis="y2",
        line=dict(color="#6B8E23", width=3),
        mode="lines+markers"
    ))
    
    fig.update_layout(
        title="Análise de Pareto: Receita por Campanha",
        xaxis=dict(title="Campanha", showticklabels=False),
        yaxis=dict(title="Receita (R$)"),
        yaxis2=dict(title="% Acumulado", overlaying="y", side="right", range=[0, 110]),
        template="plotly_dark",
        plot_bgcolor="#0a0a0a",
        paper_bgcolor="#0a0a0a",
        font=dict(color="#ffffff"),
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
    
    # Escala de cores customizada (vermelho -> verde militar -> verde)
    custom_colorscale = [
        [0, "#f53d3d"],
        [0.3, "#ff9800"],
        [0.5, "#556B2F"],
        [0.7, "#6B8E23"],
        [1, "#00a650"]
    ]
    
    # Criar figura com Treemap usando path e values
    fig = px.treemap(
        df_plot,
        path=["Quadrante", "Nome"],
        values="Investimento",
        color="ROAS_Real",
        color_continuous_scale=custom_colorscale,
        title="Alocacao de Investimento por Campanha (Tamanho = Investimento, Cor = ROAS)",
        template="plotly_dark",
        color_continuous_midpoint=5,
        hover_name="Nome"
    )
    
    fig.update_traces(textposition="middle center", textfont_size=10, textfont_color="#ffffff")
    fig.update_layout(
        margin=dict(l=20, r=20, t=40, b=20),
        plot_bgcolor="#0a0a0a",
        paper_bgcolor="#0a0a0a",
        font=dict(color="#ffffff"),
        coloraxis_colorbar=dict(title="ROAS", tickfont=dict(color="#ffffff"))
    )
    st.plotly_chart(fig, use_container_width=True)

def main():
    st.set_page_config(page_title="Mercado Livre Ads", layout="wide", initial_sidebar_state="expanded")

    # Carregar CSS customizado
    try:
        with open(".streamlit/style.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("Arquivo de estilo não encontrado. O dashboard será exibido com o tema padrão.")

    st.title("📊 Mercado Livre Ads - Dashboard e Relatório")

    with st.sidebar:
        st.caption(f"Atualizado em {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        st.divider()

        st.subheader("Arquivos")
        organico_file = st.file_uploader("Relatorio de Desempenho de Anúncios (Excel)", type=["xlsx"])
        patrocinados_file = st.file_uploader("Relatorio Anuncios Patrocinados (Excel)", type=["xlsx"])
        campanhas_file = st.file_uploader("Relatorio de Campanha (Excel)", type=["xlsx"])
        
        st.divider()
        st.subheader("Comparativo (Opcional)")
        snapshot_file = st.file_uploader("Snapshot de Referencia (Excel)", type=["xlsx"], help="Arquivo gerado ha 15 dias para comparar evolucao (Snapshot v2)")
        st.divider()
        st.subheader("Estoque (Opcional)")
        usar_estoque = st.checkbox("Ativar visão de estoque", value=False)
        estoque_file = st.file_uploader("Arquivo de estoque (Excel)", type=["xlsx"], disabled=not usar_estoque)
        if usar_estoque:
            cA, cB, cC = st.columns(3)
            with cA:
                estoque_min_ads = st.number_input("Mínimo p/ entrar em Ads (un)", min_value=0, value=6, step=1)
            with cB:
                estoque_baixo = st.number_input("Estoque baixo (un)", min_value=0, value=6, step=1)
            with cC:
                estoque_critico = st.number_input("Estoque crítico (un)", min_value=0, value=3, step=1)
            
            tratar_estoque_vazio_como_zero = st.checkbox("Tratar estoque vazio como 0", value=False)

        st.divider()
        st.subheader("Snapshot V2 - Ações")
        baixar_snapshot_auto = st.checkbox("Baixar Snapshot automaticamente", value=False)

    # Validação de entrada
    if organico_file is None or patrocinados_file is None or campanhas_file is None:
        st.info("Por favor, carregue os três arquivos de relatório para começar.")
        return

    try:
        # -------------------------
        # Carregamento de Dados
        # -------------------------
        ads_panel, kpis = ml.load_ads_report(organico_file)
        camp_strat = ml.load_campaigns_report(campanhas_file)
        
        # Merge: Enriquecer camp_strat com dados de patrocinados
        camp_strat = ml.merge_campaign_ads(camp_strat, patrocinados_file)
        
        # Classificação de Quadrantes
        camp_strat = ml.classify_quadrants(camp_strat, kpis)
        
        # -------------------------
        # Snapshot V2 - Carregamento e Comparação
        # -------------------------
        camp_snap, anuncio_snap, kpis_snap = ml.load_snapshot_v2(snapshot_file)
        
        camp_strat_comp = ml.compare_snapshots_campanha(camp_strat, camp_snap)
        ads_panel_comp = ml.compare_snapshots_anuncio(ads_panel, anuncio_snap)

        # -------------------------
        # Snapshot V2 - Salvamento Automático
        # -------------------------
        if baixar_snapshot_auto:
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
        # Estoque (opcional) - ajuste apenas para exibicao
        # -------------------------
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
    # Sumário Executivo
    # -------------------------
    st.header("Sumário Executivo")
    
    # Geração do texto do sumário
    def generate_executive_summary(kpis, camp_strat_comp, ads_panel_comp):
        invest_ads = float(kpis.get("Investimento Ads (R$)", 0))
        receita_ads = float(kpis.get("Receita Ads (R$)", 0))
        roas_val = float(kpis.get("ROAS", 0))
        tacos_pct = float(kpis.get("TACOS", 0)) * 100
        
        # Análise de Quadrantes
        q_counts = camp_strat_comp["Quadrante"].value_counts()
        q_hemorragia = q_counts.get("HEMORRAGIA", 0)
        q_escala = q_counts.get("ESCALA", 0)
        
        # Análise de Migração (Protegida contra colunas ausentes)
        migracao_text = ""
        if "Migracao_Quadrante" in camp_strat_comp.columns:
            migracao_melhora = camp_strat_comp[camp_strat_comp["Migracao_Quadrante"].str.contains("HEMORRAGIA PARA ESTÁVEL|HEMORRAGIA PARA ESCALA|ESTÁVEL PARA ESCALA", na=False)].shape[0]
            migracao_piora = camp_strat_comp[camp_strat_comp["Migracao_Quadrante"].str.contains("ESTÁVEL PARA HEMORRAGIA|ESCALA PARA HEMORRAGIA", na=False)].shape[0]
            migracao_text = f"""
        **Evolução (Comparativo com Snapshot):**
        - **{migracao_melhora}** campanhas apresentaram melhora na classificação de quadrante (ex: saíram de Hemorragia).
        - **{migracao_piora}** campanhas apresentaram piora na classificação, indicando a necessidade de revisão das ações tomadas.
            """
        
        # Análise de Anúncios
        ads_pausar = ads_panel_comp[ads_panel_comp["Acao_Anuncio"] == "Pausar anúncio"].shape[0] if "Acao_Anuncio" in ads_panel_comp.columns else 0
        ads_vencedores = ads_panel_comp[ads_panel_comp["Status_Anuncio"] == "Vencedor"].shape[0] if "Status_Anuncio" in ads_panel_comp.columns else 0
        
        summary = f"""
        A performance geral da sua conta de Mercado Livre Ads apresenta um **ROAS de {fmt_number_br(roas_val, 2)}x** e um **TACOS de {fmt_percent_br(tacos_pct)}**. 
        No total, foram investidos **{fmt_money_br(invest_ads)}** e gerados **{fmt_money_br(receita_ads)}** em receita direta de Ads.
        
        **Análise de Campanhas:**
        - Atualmente, **{q_hemorragia}** campanhas estão classificadas como **HEMORRAGIA** (baixo ROAS), exigindo atenção imediata.
        - **{q_escala}** campanhas estão prontas para **ESCALA** (ROAS forte com perda por orçamento).
        {migracao_text}
        **Análise Tática (Anúncios):**
        - Foram identificados **{ads_vencedores}** anúncios vencedores que devem ser preservados.
        - **{ads_pausar}** anúncios estão recomendados para pausa imediata por baixo desempenho e alto investimento.
        
        O plano de ação de 15 dias foca em resolver as campanhas em Hemorragia e maximizar o potencial das campanhas em Escala.
        """
        return summary
    
    st.markdown(generate_executive_summary(kpis, camp_strat_comp, ads_panel_comp))
    
    st.divider()
    
    # -------------------------
    # KPIs
    # -------------------------
    st.header("Indicadores Chave de Performance (KPIs)")
    cols = st.columns(4)

    invest_ads = float(kpis.get("Investimento Ads (R$)", 0))
    receita_ads = float(kpis.get("Receita Ads (R$)", 0))
    roas_val = float(kpis.get("ROAS", 0))
    tacos_val = float(kpis.get("TACOS", 0))
    tacos_pct = tacos_val * 100 if tacos_val <= 2 else tacos_val

    cols[0].metric("💰 Investimento Ads", fmt_money_br(invest_ads))
    cols[1].metric("📈 Receita Ads", fmt_money_br(receita_ads))
    
    # ROAS com cor dinâmica
    roas_label = "Bom" if roas_val >= 5 else "Abaixo da meta"
    cols[2].metric(
        "🎯 ROAS", 
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
    
    cols[3].metric("📉 TACOS", fmt_percent_br(tacos_pct), delta=tacos_label, delta_color=tacos_color)

    st.divider()

    # -------------------------
    # Funil de Conversão
    # -------------------------
    st.header("🎯 Funil de Conversão")
    if camp_strat is not None and not camp_strat.empty:
        # Extrair métricas do funil
        impressoes = camp_strat["Impressões"].sum() if "Impressões" in camp_strat.columns else 0
        cliques = camp_strat["Cliques"].sum() if "Cliques" in camp_strat.columns else 0
        vendas = camp_strat["Qtd_Vendas"].sum() if "Qtd_Vendas" in camp_strat.columns else 0
        
        ctr = (cliques / impressoes * 100) if impressoes > 0 else 0
        cpc = (invest_ads / cliques) if cliques > 0 else 0
        taxa_conversao = (vendas / cliques * 100) if cliques > 0 else 0
        cpa = (invest_ads / vendas) if vendas > 0 else 0
        
        # Layout: Funil + Métricas ao lado
        col_funnel, col_metrics = st.columns([2, 1])
        
        with col_funnel:
            # Criar funil com Plotly
            fig_funnel = go.Figure(go.Funnel(
                y=['Atração', 'Conversão', 'Venda'],
                x=[int(impressoes), int(cliques), int(vendas)],
                marker=dict(
                    color=['#FFA500', '#FF6B35', '#1a1a1a'],
                    line=dict(color='white', width=2)
                ),
                textposition="inside",
                textinfo="value+percent initial",
                textfont=dict(color='white', size=14),
                connector=dict(line=dict(color="#556B2F", width=2))
            ))
            
            fig_funnel.update_layout(
                plot_bgcolor="#0a0a0a",
                paper_bgcolor="#0a0a0a",
                font=dict(color="#ffffff", size=12),
                height=350,
                margin=dict(l=30, r=30, t=30, b=30),
                showlegend=False
            )
            
            st.plotly_chart(fig_funnel, use_container_width=True)
        
        with col_metrics:
            st.metric("CTR", fmt_percent_br(ctr))
            st.metric("CPC", fmt_money_br(cpc))
            st.metric("Taxa Conv.", fmt_percent_br(taxa_conversao))
            st.metric("CPA", fmt_money_br(cpa))
    
    st.divider()

    # -------------------------
    # Gráficos de Análise
    # -------------------------
    st.header("Análise Visual de Performance")
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        render_pareto_chart(camp_strat)
    
    with col_g2:
        render_treemap_chart(camp_strat)

    st.divider()

    # -------------------------
    # Painel geral
    # -------------------------
    with st.expander("Painel Geral de Campanhas", expanded=True):
        panel_raw = ml.build_control_panel(camp_strat)
        panel_raw = replace_acos_obj_with_roas_obj(panel_raw)
        panel_view = prepare_df_for_view(panel_raw, drop_cpi_cols=True, drop_roas_generic=False)
        st.dataframe(format_table_br(panel_view), use_container_width=True)

    st.divider()

    # -------------------------
    # Matriz CPI
    # -------------------------
    with st.expander("Matriz CPI (Oportunidades de Otimização)", expanded=False):
        cpi_raw = replace_acos_obj_with_roas_obj(camp_strat)
        cpi_view = prepare_df_for_view(cpi_raw, drop_cpi_cols=True, drop_roas_generic=True)
        st.dataframe(format_table_br(cpi_view), use_container_width=True)

    st.divider()

    # -------------------------
    # Nível de anúncio (Patrocinados)
    # -------------------------
    with st.expander("🎯 Análise Tática por Anúncio (Ads)", expanded=False):
        ads_view = prepare_df_for_view(ads_panel_comp, drop_cpi_cols=False, drop_roas_generic=False)
        st.dataframe(format_table_br(ads_view), use_container_width=True)

    st.divider()

    # -------------------------
    # Recomendações de Ação
    # -------------------------
    with st.expander("📋 Recomendações de Ação", expanded=False):
        st.subheader("Campanhas para Pausar (HEMORRAGIA)")
        pause = camp_strat_comp[camp_strat_comp["Quadrante"] == "HEMORRAGIA"].copy()
        if not pause.empty:
            pause_view = prepare_df_for_view(pause, drop_cpi_cols=True, drop_roas_generic=False)
            st.dataframe(format_table_br(pause_view), use_container_width=True)
        else:
            st.success("Nenhuma campanha em HEMORRAGIA. Parabéns!")

        st.subheader("Campanhas para Escalar (ESCALA)")
        scale = camp_strat_comp[camp_strat_comp["Quadrante"] == "ESCALA"].copy()
        if not scale.empty:
            scale_view = prepare_df_for_view(scale, drop_cpi_cols=True, drop_roas_generic=False)
            st.dataframe(format_table_br(scale_view), use_container_width=True)
        else:
            st.info("Nenhuma campanha pronta para escalar no momento.")

        st.subheader("Campanhas Estáveis (ESTÁVEL)")
        estavel = camp_strat_comp[camp_strat_comp["Quadrante"] == "ESTÁVEL"].copy()
        if not estavel.empty:
            estavel_view = prepare_df_for_view(estavel, drop_cpi_cols=True, drop_roas_generic=False)
            st.dataframe(format_table_br(estavel_view), use_container_width=True)
        else:
            st.info("Nenhuma campanha em situação estável.")

        st.subheader("Anúncios para Pausar (Baixo Desempenho)")
        acos = ads_panel_comp[ads_panel_comp["Acao_Anuncio"] == "Pausar anúncio"].copy()
        if not acos.empty:
            acos_view = prepare_df_for_view(acos, drop_cpi_cols=False, drop_roas_generic=False)
            st.dataframe(format_table_br(acos_view), use_container_width=True)
        else:
            st.success("Nenhum anúncio recomendado para pausa.")

        st.subheader("Anúncios Vencedores (Melhor Desempenho)")
        vencedores = ads_panel_comp[ads_panel_comp["Status_Anuncio"] == "Vencedor"].copy()
        if not vencedores.empty:
            vencedores_view = prepare_df_for_view(vencedores, drop_cpi_cols=False, drop_roas_generic=False)
            st.dataframe(format_table_br(vencedores_view), use_container_width=True)
        else:
            st.info("Nenhum anúncio vencedor identificado.")

    st.divider()

    # -------------------------
    # Estoque (opcional)
    # -------------------------
    if "usar_estoque" in locals() and usar_estoque and not blocked_stock.empty:
        with st.expander("⚠️ Anúncios Bloqueados por Estoque", expanded=False):
            st.dataframe(format_table_br(blocked_stock), use_container_width=True)

if __name__ == "__main__":
    main()
