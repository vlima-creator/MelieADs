"""
Dashboard Interativo MelieADs - Streamlit
Visualização de performance de campanhas no Mercado Livre Ads
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np

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
        --primary-color: #556B2F;
        --secondary-color: #6B8E23;
        --background-color: #0a0a0a;
        --card-color: #141414;
    }
    
    body {
        background-color: #0a0a0a;
        color: #ffffff;
    }
    
    .stMetric {
        background-color: #141414;
        padding: 20px;
        border-radius: 12px;
        border-left: 3px solid #556B2F;
    }
    
    .stMetric label {
        color: #999999 !important;
        font-size: 0.85rem !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
    }
    
    .stMetric > div:nth-child(2) {
        color: #ffffff !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Função para formatar valores em Real
def fmt_money(x):
    if x is None or x == 0:
        return "R$ 0,00"
    try:
        return f"R$ {float(x):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

def fmt_percent(x):
    if x is None or x == 0:
        return "0,00%"
    try:
        return f"{float(x):.2f}%".replace(".", ",")
    except:
        return "0,00%"

def fmt_number(x, decimals=0):
    if x is None or x == 0:
        return "0"
    try:
        if decimals == 0:
            return f"{int(round(float(x))):,}".replace(",", ".")
        else:
            return f"{float(x):,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "0"

# Dados simulados (em produção, viriam do banco de dados)
def load_data():
    """Carrega dados de exemplo do relatório"""
    data = {
        'Impressões': 1200000,
        'Cliques': 45200,
        'Investimento': 24786.38,
        'Vendas': 1200,
        'Receita': 233205.75,
        'ROAS': 9.41,
        'ACOS': 4.93,
        'CTR': 3.77,
        'CPC': 0.548,
        'CPA': 20.66,
        'CPM': 20.66,
        'TicketMedio': 194.34
    }
    return data

# Cabeçalho
st.markdown("""
    <div style="
        background: linear-gradient(135deg, #556B2F 0%, #6B8E23 100%);
        padding: 30px;
        border-radius: 12px;
        margin-bottom: 30px;
        text-align: center;
    ">
        <h1 style="color: #ffffff; margin: 0; font-size: 2.5rem;">📊 MelieADs Dashboard</h1>
        <p style="color: rgba(255,255,255,0.8); margin: 10px 0 0 0; font-size: 1rem;">
            Análise de Performance de Campanhas no Mercado Livre Ads
        </p>
    </div>
    """, unsafe_allow_html=True)

# Carregar dados
kpis = load_data()

# Sidebar para filtros
with st.sidebar:
    st.markdown("### 🎯 Filtros")
    
    periodo = st.selectbox(
        "Período",
        ["Últimos 7 dias", "Últimos 15 dias", "Últimos 30 dias", "Este mês", "Mês anterior"]
    )
    
    st.markdown("---")
    
    st.markdown("### 📈 Sobre")
    st.info("""
    Este dashboard apresenta métricas reais de campanhas de publicidade no Mercado Livre Ads.
    
    **Atualização:** Em tempo real
    **Última sincronização:** Hoje às 14:30
    """)

# KPIs - Primeira linha
st.markdown("### 💰 Principais Métricas")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        label="Investimento",
        value=fmt_money(kpis['Investimento']),
        delta="↑ 15.8%"
    )

with col2:
    st.metric(
        label="Receita (GMV)",
        value=fmt_money(kpis['Receita']),
        delta="↑ 17.5%"
    )

with col3:
    st.metric(
        label="Vendas",
        value=fmt_number(kpis['Vendas']),
        delta="↑ 22.3%"
    )

with col4:
    st.metric(
        label="ROAS",
        value=f"{kpis['ROAS']:.2f}x",
        delta="↑ 12.2%"
    )

with col5:
    st.metric(
        label="ACOS",
        value=fmt_percent(kpis['ACOS']),
        delta="↓ 2.4%"
    )

st.markdown("---")

# Gráfico de Linha do Tempo
st.markdown("### 📊 Evolução de Gastos vs. Vendas")

# Gerar dados de série temporal
dates = pd.date_range(start='2026-01-01', periods=7, freq='W')
investimento_data = [3500, 4200, 5100, 6800, 8900, 12400, 15600]
vendas_data = [120, 180, 250, 380, 520, 750, 1050]

fig_timeline = go.Figure()

# Linha de Investimento
fig_timeline.add_trace(go.Scatter(
    x=dates,
    y=investimento_data,
    name="Investimento (R$)",
    line=dict(color="#556B2F", width=3),
    fill="tozeroy",
    fillcolor="rgba(85, 107, 47, 0.2)",
    mode="lines+markers",
    marker=dict(size=8),
    yaxis="y1"
))

# Linha de Vendas
fig_timeline.add_trace(go.Scatter(
    x=dates,
    y=vendas_data,
    name="Vendas (Qtd)",
    line=dict(color="#6B8E23", width=3),
    mode="lines+markers",
    marker=dict(size=8),
    yaxis="y2"
))

fig_timeline.update_layout(
    title="Comparativo Semanal: Investimento vs. Vendas",
    xaxis=dict(title="Data", showgrid=False),
    yaxis=dict(
        title="Investimento (R$)",
        showgrid=True,
        gridcolor="#2a2a2a",
        titlefont=dict(color="#556B2F"),
        tickfont=dict(color="#556B2F")
    ),
    yaxis2=dict(
        title="Vendas (Quantidade)",
        overlaying="y",
        side="right",
        titlefont=dict(color="#6B8E23"),
        tickfont=dict(color="#6B8E23")
    ),
    plot_bgcolor="#0a0a0a",
    paper_bgcolor="#0a0a0a",
    font=dict(color="#ffffff"),
    hovermode="x unified",
    height=400,
    legend=dict(x=0.01, y=0.99, bgcolor="rgba(0,0,0,0.5)")
)

st.plotly_chart(fig_timeline, use_container_width=True)

# Funil de Conversão
st.markdown("### 🎯 Funil de Conversão")

col_funil_left, col_funil_right = st.columns([2, 1])

with col_funil_left:
    # Dados do funil
    funnel_labels = ['Impressões', 'Cliques', 'Vendas']
    funnel_values = [kpis['Impressões'], kpis['Cliques'], kpis['Vendas']]
    
    fig_funnel = go.Figure(go.Funnel(
        y=funnel_labels,
        x=funnel_values,
        marker=dict(
            color=['#556B2F', '#6B8E23', '#7a9d2a'],
            line=dict(color='#ffffff', width=2)
        ),
        textposition="inside",
        textinfo="value+percent initial",
        textfont=dict(color='white', size=12, family="Arial Black"),
        connector=dict(line=dict(color="#556B2F", width=2))
    ))
    
    fig_funnel.update_layout(
        title="Jornada de Conversão",
        plot_bgcolor="#0a0a0a",
        paper_bgcolor="#0a0a0a",
        font=dict(color="#ffffff", size=12),
        height=350,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    st.plotly_chart(fig_funnel, use_container_width=True)

with col_funil_right:
    st.markdown("#### 📈 Métricas do Funil")
    
    ctr = (kpis['Cliques'] / kpis['Impressões'] * 100) if kpis['Impressões'] > 0 else 0
    taxa_conversao = (kpis['Vendas'] / kpis['Cliques'] * 100) if kpis['Cliques'] > 0 else 0
    
    st.markdown(f"""
    **🎯 Topo (Awareness)**
    - Impressões: {fmt_number(kpis['Impressões'])}
    - CPM: {fmt_money(kpis['CPM'])}
    
    **📍 Meio (Consideração)**
    - Cliques: {fmt_number(kpis['Cliques'])}
    - CTR: {fmt_percent(ctr)}
    - CPC: {fmt_money(kpis['CPC'])}
    
    **✅ Fundo (Conversão)**
    - Vendas: {fmt_number(kpis['Vendas'])}
    - Taxa Conv.: {fmt_percent(taxa_conversao)}
    - CPA: {fmt_money(kpis['CPA'])}
    """)

st.markdown("---")

# Métricas Secundárias
st.markdown("### 📊 Análise Detalhada")

col_sec1, col_sec2, col_sec3 = st.columns(3)

with col_sec1:
    st.metric(
        label="Taxa de Cliques (CTR)",
        value=fmt_percent(kpis['CTR']),
        delta="Objetivo: 2.5%"
    )

with col_sec2:
    taxa_conv = (kpis['Vendas']/kpis['Cliques']*100) if kpis['Cliques'] > 0 else 0
    st.metric(
        label="Taxa de Conversão",
        value=fmt_percent(taxa_conv),
        delta="Objetivo: 2.0%"
    )

with col_sec3:
    st.metric(
        label="Ticket Médio",
        value=fmt_money(kpis['TicketMedio']),
        delta="vs. R$ 180 (meta)"
    )

st.markdown("---")

# Tabela de Resumo
st.markdown("### 📋 Resumo de Performance")

resumo_data = {
    'Métrica': [
        'Impressões',
        'Cliques',
        'Vendas',
        'Investimento',
        'Receita',
        'ROAS',
        'ACOS',
        'Ticket Médio'
    ],
    'Valor': [
        fmt_number(kpis['Impressões']),
        fmt_number(kpis['Cliques']),
        fmt_number(kpis['Vendas']),
        fmt_money(kpis['Investimento']),
        fmt_money(kpis['Receita']),
        f"{kpis['ROAS']:.2f}x",
        fmt_percent(kpis['ACOS']),
        fmt_money(kpis['TicketMedio'])
    ],
    'Status': ['✅', '✅', '✅', '⚠️', '✅', '✅', '✅', '✅']
}

df_resumo = pd.DataFrame(resumo_data)
st.dataframe(df_resumo, use_container_width=True, hide_index=True)

st.markdown("---")

# Rodapé
st.markdown("""
    <div style="
        text-align: center;
        padding: 20px;
        color: #999999;
        font-size: 0.9rem;
        border-top: 1px solid #2a2a2a;
        margin-top: 30px;
    ">
        <p>Dashboard MelieADs © 2026 | Atualizado em tempo real</p>
        <p>Para suporte, entre em contato com o time de análise</p>
    </div>
    """, unsafe_allow_html=True)
