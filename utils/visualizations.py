#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de visualizações com Plotly
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Dict, List


def criar_grafico_evolucao_categoria(df: pd.DataFrame) -> go.Figure:
    """Cria gráfico de evolução da categoria ao longo do tempo"""
    if df.empty:
        return go.Figure()
    
    fig = go.Figure()
    
    # Faturamento
    fig.add_trace(go.Scatter(
        x=df['periodo'],
        y=df['faturamento'],
        name='Faturamento',
        mode='lines+markers',
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=8),
        yaxis='y1'
    ))
    
    # Unidades
    fig.add_trace(go.Scatter(
        x=df['periodo'],
        y=df['unidades'],
        name='Unidades',
        mode='lines+markers',
        line=dict(color='#ff7f0e', width=3),
        marker=dict(size=8),
        yaxis='y2'
    ))
    
    fig.update_layout(
        title='Evolução da Categoria (Macro)',
        xaxis=dict(title='Período'),
        yaxis=dict(
            title='Faturamento (R$)',
            side='left',
            showgrid=True
        ),
        yaxis2=dict(
            title='Unidades',
            side='right',
            overlaying='y',
            showgrid=False
        ),
        hovermode='x unified',
        height=400,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    
    return fig


def criar_grafico_ticket_medio(df: pd.DataFrame) -> go.Figure:
    """Cria gráfico de evolução do ticket médio"""
    if df.empty:
        return go.Figure()
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['periodo'],
        y=df['ticket_medio'],
        name='Ticket Médio',
        mode='lines+markers',
        line=dict(color='#2ca02c', width=3),
        marker=dict(size=10),
        fill='tozeroy',
        fillcolor='rgba(44, 160, 44, 0.2)'
    ))
    
    fig.update_layout(
        title='Evolução do Ticket Médio da Categoria',
        xaxis=dict(title='Período'),
        yaxis=dict(title='Ticket Médio (R$)'),
        hovermode='x unified',
        height=350
    )
    
    return fig


def criar_grafico_ranking_subcategorias(df: pd.DataFrame) -> go.Figure:
    """Cria gráfico de barras horizontal com ranking de subcategorias"""
    if df.empty:
        return go.Figure()
    
    # Definir cores por status
    color_map = {
        'FOCO': '#2ecc71',
        'OK': '#f39c12',
        'EVITAR': '#e74c3c'
    }
    
    colors = [color_map.get(status, '#95a5a6') for status in df['Status']]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=df['Subcategoria'],
        x=df['Score'],
        orientation='h',
        marker=dict(
            color=colors,
            line=dict(color='rgba(0,0,0,0.3)', width=1)
        ),
        text=df['Score'].apply(lambda x: f'{x:.2f}'),
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>Score: %{x:.3f}<extra></extra>'
    ))
    
    fig.update_layout(
        title='Ranking de Subcategorias por Score',
        xaxis=dict(title='Score', range=[0, 1.1]),
        yaxis=dict(title='', autorange='reversed'),
        height=max(400, len(df) * 40),
        showlegend=False
    )
    
    return fig


def criar_grafico_mercado_subcategorias(df: pd.DataFrame) -> go.Figure:
    """Cria gráfico de pizza/treemap com tamanho de mercado"""
    if df.empty:
        return go.Figure()
    
    # Usar apenas top 10 para visualização
    df_top = df.head(10).copy()
    
    fig = px.treemap(
        df_top,
        path=['Subcategoria'],
        values='Mercado (R$)',
        color='Score',
        color_continuous_scale='RdYlGn',
        title='Tamanho de Mercado por Subcategoria'
    )
    
    fig.update_traces(
        textinfo='label+value+percent root',
        texttemplate='<b>%{label}</b><br>R$ %{value:,.0f}<br>%{percentRoot}'
    )
    
    fig.update_layout(height=500)
    
    return fig


def criar_grafico_cenarios(df_cenarios: pd.DataFrame) -> go.Figure:
    """Cria gráfico comparativo de cenários"""
    if df_cenarios.empty:
        return go.Figure()
    
    fig = go.Figure()
    
    # Receita Projetada
    fig.add_trace(go.Bar(
        name='Receita 6M',
        x=df_cenarios['Cenário'],
        y=df_cenarios['Receita Projetada 6M'],
        marker=dict(color='#3498db'),
        text=df_cenarios['Receita Projetada 6M'].apply(lambda x: f'R$ {x:,.0f}'),
        textposition='outside'
    ))
    
    # Lucro Projetado
    fig.add_trace(go.Bar(
        name='Lucro 6M',
        x=df_cenarios['Cenário'],
        y=df_cenarios['Lucro Projetado 6M'],
        marker=dict(color='#2ecc71'),
        text=df_cenarios['Lucro Projetado 6M'].apply(lambda x: f'R$ {x:,.0f}'),
        textposition='outside'
    ))
    
    fig.update_layout(
        title='Comparação de Cenários - Receita e Lucro Projetados',
        xaxis=dict(title='Cenário'),
        yaxis=dict(title='Valor (R$)'),
        barmode='group',
        height=450,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    
    return fig


def criar_grafico_crescimento(df_cenarios: pd.DataFrame) -> go.Figure:
    """Cria gráfico de crescimento percentual"""
    if df_cenarios.empty:
        return go.Figure()
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=df_cenarios['Cenário'],
        y=df_cenarios['Crescimento (%)'],
        marker=dict(
            color=df_cenarios['Crescimento (%)'],
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title='Crescimento %')
        ),
        text=df_cenarios['Crescimento (%)'].apply(lambda x: f'{x:,.1f}%'),
        textposition='outside'
    ))
    
    fig.update_layout(
        title='Crescimento Percentual vs Situação Atual',
        xaxis=dict(title='Cenário'),
        yaxis=dict(title='Crescimento (%)'),
        height=400
    )
    
    return fig


def criar_gauge_score(score: float, status: str) -> go.Figure:
    """Cria indicador gauge para o score"""
    # Definir cor baseada no status
    color_map = {
        'FOCO': '#2ecc71',
        'OK': '#f39c12',
        'EVITAR': '#e74c3c'
    }
    
    color = color_map.get(status, '#95a5a6')
    
    fig = go.Figure(go.Indicator(
        mode='gauge+number+delta',
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': f'Score de Priorização<br><span style="font-size:0.8em;color:{color}">{status}</span>'},
        number={'font': {'size': 50}},
        gauge={
            'axis': {'range': [0, 1], 'tickwidth': 1},
            'bar': {'color': color},
            'steps': [
                {'range': [0, 0.4], 'color': '#ffcccc'},
                {'range': [0.4, 0.7], 'color': '#fff3cd'},
                {'range': [0.7, 1], 'color': '#d4edda'}
            ],
            'threshold': {
                'line': {'color': 'red', 'width': 4},
                'thickness': 0.75,
                'value': 0.7
            }
        }
    ))
    
    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=60, b=20)
    )
    
    return fig


def criar_comparacao_tickets(ticket_mercado: float, ticket_cliente: float, 
                             limite_inf: float, limite_sup: float) -> go.Figure:
    """Cria gráfico comparativo de tickets"""
    
    fig = go.Figure()
    
    # Área de range permitido
    fig.add_trace(go.Scatter(
        x=['Limite Inferior', 'Limite Superior'],
        y=[limite_inf, limite_sup],
        fill='tozeroy',
        fillcolor='rgba(46, 204, 113, 0.2)',
        line=dict(color='rgba(46, 204, 113, 0.4)', width=0),
        name='Range Permitido',
        showlegend=True
    ))
    
    # Ticket Mercado
    fig.add_trace(go.Scatter(
        x=['Ticket Mercado'],
        y=[ticket_mercado],
        mode='markers',
        marker=dict(size=20, color='#3498db', symbol='diamond'),
        name='Ticket Mercado',
        text=[f'R$ {ticket_mercado:,.2f}'],
        textposition='top center'
    ))
    
    # Ticket Cliente
    fig.add_trace(go.Scatter(
        x=['Ticket Cliente'],
        y=[ticket_cliente],
        mode='markers',
        marker=dict(size=20, color='#e74c3c', symbol='circle'),
        name='Ticket Cliente',
        text=[f'R$ {ticket_cliente:,.2f}'],
        textposition='top center'
    ))
    
    fig.update_layout(
        title='Comparação de Tickets - Cliente vs Mercado',
        xaxis=dict(title=''),
        yaxis=dict(title='Valor (R$)'),
        height=350,
        showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    
    return fig
