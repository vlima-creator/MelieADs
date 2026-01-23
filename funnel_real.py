"""
Função para renderizar o funil com métricas reais do relatório usando Plotly
"""
import streamlit as st
import plotly.graph_objects as go

def fmt_money_br(x):
    if x is None or (hasattr(x, '__iter__') and len(str(x)) == 0):
        return "R$ 0,00"
    try:
        return f"R$ {float(x):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

def fmt_percent_br(x):
    if x is None or (hasattr(x, '__iter__') and len(str(x)) == 0):
        return "0,00%"
    try:
        return f"{float(x):.2f}%".replace(".", ",")
    except:
        return "0,00%"

def fmt_number_br(x, decimals=2):
    if x is None or (hasattr(x, '__iter__') and len(str(x)) == 0):
        return "0,00"
    try:
        return f"{float(x):,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "0,00"

def fmt_int_br(x):
    if x is None or (hasattr(x, '__iter__') and len(str(x)) == 0):
        return "0"
    try:
        return f"{int(round(float(x))):,}".replace(",", ".")
    except:
        return "0"

def render_funnel_chart_real(kpis, camp_agg):
    """Renderiza um funil visual com Plotly baseado em métricas reais do relatório."""
    
    # Extrair métricas reais dos dados
    impressoes = camp_agg["Impressões"].sum() if "Impressões" in camp_agg.columns else 0
    cliques = camp_agg["Cliques"].sum() if "Cliques" in camp_agg.columns else 0
    investimento = float(kpis.get("Investimento Ads (R$)", 0))
    receita = float(kpis.get("Receita Ads (R$)", 0))
    vendas = camp_agg["Qtd_Vendas"].sum() if "Qtd_Vendas" in camp_agg.columns else 0
    roas = float(kpis.get("ROAS", 0))
    tacos = float(kpis.get("TACOS", 0))
    
    # Calcular métricas derivadas
    ctr = (cliques / impressoes * 100) if impressoes > 0 else 0
    cpc = (investimento / cliques) if cliques > 0 else 0
    taxa_conversao = (vendas / cliques * 100) if cliques > 0 else 0
    cpa = (investimento / vendas) if vendas > 0 else 0
    ticket_medio = (receita / vendas) if vendas > 0 else 0
    cpm = (investimento / impressoes * 1000) if impressoes > 0 else 0
    
    # Criar funil com Plotly
    fig = go.Figure(go.Funnel(
        y=['Impressões<br>(Topo)', 'Cliques<br>(Meio)', 'Vendas<br>(Fundo)'],
        x=[int(impressoes), int(cliques), int(vendas)],
        marker=dict(
            color=['#556B2F', '#6B8E23', '#7a9d2a'],
            line=dict(color='white', width=2)
        ),
        textposition="inside",
        textinfo="value+percent initial",
        textfont=dict(color='white', size=12, family="Arial Black"),
        connector=dict(line=dict(color="#556B2F", width=2)),
        hovertemplate="<b>%{y}</b><br>Quantidade: %{value:,}<br>Percentual: %{percentInitial}<extra></extra>"
    ))
    
    fig.update_layout(
        title=dict(
            text="<b>Funil de Conversão</b><br><sub>Jornada de Compra</sub>",
            font=dict(size=16, color="#556B2F"),
            x=0.5,
            xanchor="center"
        ),
        plot_bgcolor="#0a0a0a",
        paper_bgcolor="#0a0a0a",
        font=dict(color="#ffffff", size=12),
        height=450,
        margin=dict(l=50, r=50, t=80, b=50),
        showlegend=False
    )
    
    # Renderizar gráfico
    st.plotly_chart(fig, use_container_width=True)
    
    # Métricas do funil em colunas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="CTR",
            value=fmt_percent_br(ctr),
            delta="Meta: 2.5%"
        )
    
    with col2:
        st.metric(
            label="CPC",
            value=fmt_money_br(cpc),
            delta="Custo por Clique"
        )
    
    with col3:
        st.metric(
            label="Taxa de Conversão",
            value=fmt_percent_br(taxa_conversao),
            delta="Meta: 2.0%"
        )
    
    with col4:
        st.metric(
            label="CPA",
            value=fmt_money_br(cpa),
            delta="Custo por Aquisição"
        )
    
    # Resumo de eficiência
    st.markdown("---")
    
    col_eff1, col_eff2, col_eff3, col_eff4 = st.columns(4)
    
    with col_eff1:
        st.metric(
            label="ROAS",
            value=f"{fmt_number_br(roas, 2)}x",
            delta="Retorno sobre Investimento"
        )
    
    with col_eff2:
        st.metric(
            label="Investimento Total",
            value=fmt_money_br(investimento),
            delta="Valor Gasto"
        )
    
    with col_eff3:
        st.metric(
            label="Receita Total",
            value=fmt_money_br(receita),
            delta="GMV Gerado"
        )
    
    with col_eff4:
        st.metric(
            label="Ticket Médio",
            value=fmt_money_br(ticket_medio),
            delta="Valor Médio por Venda"
        )
