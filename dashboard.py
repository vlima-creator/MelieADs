import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px

# Configuração da página
st.set_page_config(
    page_title="MelieADs Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado para tema verde militar
st.markdown("""
    <style>
    :root {
        --primary-green: #556B2F;
        --primary-green-light: #6B8E23;
        --bg-dark: #0a0a0a;
        --bg-card: #141414;
        --text-primary: #ffffff;
        --text-secondary: #a0a0a0;
    }
    
    body {
        background-color: var(--bg-dark);
        color: var(--text-primary);
    }
    
    .main {
        background-color: var(--bg-dark);
    }
    
    h1, h2, h3 {
        color: var(--primary-green-light);
    }
    
    .stMetric {
        background-color: var(--bg-card);
        border: 1px solid var(--primary-green);
        border-radius: 12px;
        padding: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.title("MelieADs Dashboard")
st.markdown("Análise de Performance de Campanhas - Mercado Livre Ads")

# Sidebar
st.sidebar.header("Filtros")

# Dados de exemplo
def gerar_dados_exemplo():
    """Gera dados de exemplo para o dashboard"""
    
    # Dados de KPIs
    kpis = {
        "Investimento": 24786.38,
        "Vendas": 1200,
        "Receita": 233205.75,
        "ROAS": 9.41,
        "ACOS": 4.93,
        "Campanhas": 68,
        "CTR": 2.45,
        "CPC": 1.23
    }
    
    # Dados de evolução temporal
    dias = pd.date_range(start='2026-01-01', end='2026-01-23', freq='D')
    dados_temporal = pd.DataFrame({
        'Data': dias,
        'Investimento': np.linspace(100, 24786, len(dias)),
        'Vendas': np.linspace(10, 1200, len(dias)),
        'Receita': np.linspace(500, 233205, len(dias))
    })
    
    # Dados do funil
    funil_data = {
        'Etapa': ['Impressoes', 'Cliques', 'Vendas'],
        'Quantidade': [500000, 12250, 1200],
        'Taxa': [100, 2.45, 9.80]
    }
    
    return kpis, dados_temporal, funil_data

# Carregar dados
kpis, dados_temporal, funil_data = gerar_dados_exemplo()

# ===== SEÇÃO 1: KPIs =====
st.header("KPIs Principais")

col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    st.metric(
        label="Investimento",
        value=f"R$ {kpis['Investimento']:,.2f}",
        delta="+5.2%"
    )

with col2:
    st.metric(
        label="Vendas",
        value=f"{kpis['Vendas']:,}",
        delta="+12.3%"
    )

with col3:
    st.metric(
        label="Receita",
        value=f"R$ {kpis['Receita']:,.2f}",
        delta="+8.7%"
    )

with col4:
    st.metric(
        label="ROAS",
        value=f"{kpis['ROAS']:.2f}x",
        delta="+1.2x"
    )

with col5:
    st.metric(
        label="ACOS",
        value=f"{kpis['ACOS']:.2f}%",
        delta="-0.5%"
    )

with col6:
    st.metric(
        label="Campanhas",
        value=f"{kpis['Campanhas']}",
        delta="+2"
    )

st.divider()

# ===== SEÇÃO 2: FUNIL DE VENDAS =====
st.header("Funil de Vendas")

# Criar funil com Plotly
fig_funil = go.Figure(go.Funnel(
    y=funil_data['Etapa'],
    x=funil_data['Quantidade'],
    marker=dict(
        color=['#556B2F', '#6B8E23', '#7BA428'],
        line=dict(color='white', width=2)
    ),
    text=[
        f"{funil_data['Quantidade'][0]:,} impressoes",
        f"{funil_data['Quantidade'][1]:,} cliques ({funil_data['Taxa'][1]:.2f}%)",
        f"{funil_data['Quantidade'][2]:,} vendas ({funil_data['Taxa'][2]:.2f}%)"
    ],
    textposition="inside",
    textfont=dict(color="white", size=12),
    hovertemplate="<b>%{y}</b><br>Quantidade: %{x:,}<extra></extra>"
))

fig_funil.update_layout(
    title="Funil de Conversao",
    font=dict(color="#ffffff", family="Arial"),
    plot_bgcolor="#0a0a0a",
    paper_bgcolor="#0a0a0a",
    margin=dict(l=20, r=20, t=40, b=20),
    height=400
)

st.plotly_chart(fig_funil, use_container_width=True)

# Métricas do funil
st.subheader("Metricas do Funil")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="CTR (Click-Through Rate)",
        value="2.45%",
        delta="+0.3%"
    )

with col2:
    st.metric(
        label="CPC (Custo por Clique)",
        value="R$ 2.02",
        delta="-0.15"
    )

with col3:
    st.metric(
        label="Taxa de Conversao",
        value="9.80%",
        delta="+1.2%"
    )

with col4:
    st.metric(
        label="CPA (Custo por Aquisicao)",
        value="R$ 20.66",
        delta="-1.50"
    )

st.divider()

# ===== SEÇÃO 3: GRÁFICO DE EVOLUÇÃO TEMPORAL =====
st.header("Evolucao Temporal")

fig_temporal = go.Figure()

# Adicionar linha de investimento (eixo Y esquerdo)
fig_temporal.add_trace(go.Scatter(
    x=dados_temporal['Data'],
    y=dados_temporal['Investimento'],
    name='Investimento (R$)',
    line=dict(color='#556B2F', width=3),
    yaxis='y1',
    hovertemplate="<b>Data:</b> %{x|%d/%m}<br><b>Investimento:</b> R$ %{y:,.2f}<extra></extra>"
))

# Adicionar linha de vendas (eixo Y direito)
fig_temporal.add_trace(go.Scatter(
    x=dados_temporal['Data'],
    y=dados_temporal['Vendas'],
    name='Vendas (Qtd)',
    line=dict(color='#6B8E23', width=3),
    yaxis='y2',
    hovertemplate="<b>Data:</b> %{x|%d/%m}<br><b>Vendas:</b> %{y:,}<extra></extra>"
))

fig_temporal.update_layout(
    title="Investimento vs Vendas ao Longo do Tempo",
    xaxis=dict(title="Data", gridcolor="#2a2a2a"),
    yaxis=dict(
        title="Investimento (R$)",
        titlefont=dict(color="#556B2F"),
        tickfont=dict(color="#556B2F"),
        gridcolor="#2a2a2a"
    ),
    yaxis2=dict(
        title="Vendas (Quantidade)",
        titlefont=dict(color="#6B8E23"),
        tickfont=dict(color="#6B8E23"),
        anchor="x",
        overlaying="y",
        side="right"
    ),
    hovermode="x unified",
    font=dict(color="#ffffff", family="Arial"),
    plot_bgcolor="#0a0a0a",
    paper_bgcolor="#0a0a0a",
    legend=dict(x=0.01, y=0.99, bgcolor="rgba(0,0,0,0.5)"),
    margin=dict(l=60, r=60, t=40, b=40),
    height=450
)

st.plotly_chart(fig_temporal, use_container_width=True)

st.divider()

# ===== SEÇÃO 4: RESUMO =====
st.header("Resumo de Performance")

resumo_col1, resumo_col2 = st.columns(2)

with resumo_col1:
    st.subheader("Periodo Analisado")
    st.info("""
    **Data Inicio:** 01/01/2026
    
    **Data Fim:** 23/01/2026
    
    **Duracao:** 23 dias
    """)

with resumo_col2:
    st.subheader("Recomendacoes")
    st.success("""
    Seu ROAS esta excelente (9.41x). Continue otimizando as campanhas em HEMORRAGIA.
    
    Considere escalar o orcamento das campanhas em ESCALA.
    """)

st.divider()

# Footer
st.markdown("""
---
**Dashboard MelieADs** | Ultima atualizacao: 23/01/2026 18:09
""")
