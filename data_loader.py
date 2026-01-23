"""
Módulo para carregar dados reais do relatório de campanhas
"""

import pandas as pd
import os
from pathlib import Path

def load_campaign_data():
    """
    Carrega dados de campanhas do arquivo Excel ou CSV
    Retorna um DataFrame com as campanhas
    """
    try:
        # Procurar por arquivo de relatório
        report_files = [
            'relatorio_campanhas.xlsx',
            'relatorio_campanhas.csv',
            'campanhas.xlsx',
            'campanhas.csv'
        ]
        
        for file in report_files:
            if os.path.exists(file):
                if file.endswith('.xlsx'):
                    df = pd.read_excel(file)
                else:
                    df = pd.read_csv(file)
                return df
        
        # Se não encontrar arquivo, retorna dados de exemplo
        return create_sample_data()
    
    except Exception as e:
        print(f"Erro ao carregar dados: {e}")
        return create_sample_data()

def create_sample_data():
    """Cria dados de exemplo para demonstração"""
    data = {
        'Nome': [
            'Campanha Premium - Eletrônicos',
            'Campanha Standard - Moda',
            'Campanha Eco - Sustentável',
            'Campanha Flash - Promoção'
        ],
        'Impressões': [450000, 350000, 250000, 150000],
        'Cliques': [18500, 12800, 8900, 5000],
        'Investimento': [9800, 7200, 4500, 3286.38],
        'Qtd_Vendas': [380, 280, 320, 220],
        'Receita': [92400, 68200, 78000, -4394.25],
        'ROAS': [9.43, 9.47, 17.33, -1.34],
        'Quadrante': ['Estrela', 'Estrela', 'Ouro', 'Problema']
    }
    
    return pd.DataFrame(data)

def calculate_kpis(df):
    """
    Calcula KPIs agregados a partir do DataFrame
    """
    if df is None or df.empty:
        return {}
    
    total_impressoes = df['Impressões'].sum() if 'Impressões' in df.columns else 0
    total_cliques = df['Cliques'].sum() if 'Cliques' in df.columns else 0
    total_investimento = df['Investimento'].sum() if 'Investimento' in df.columns else 0
    total_vendas = df['Qtd_Vendas'].sum() if 'Qtd_Vendas' in df.columns else 0
    total_receita = df['Receita'].sum() if 'Receita' in df.columns else 0
    
    # Calcular métricas derivadas
    ctr = (total_cliques / total_impressoes * 100) if total_impressoes > 0 else 0
    cpc = (total_investimento / total_cliques) if total_cliques > 0 else 0
    cpa = (total_investimento / total_vendas) if total_vendas > 0 else 0
    cpm = (total_investimento / total_impressoes * 1000) if total_impressoes > 0 else 0
    roas = (total_receita / total_investimento) if total_investimento > 0 else 0
    acos = (total_investimento / total_receita * 100) if total_receita > 0 else 0
    taxa_conversao = (total_vendas / total_cliques * 100) if total_cliques > 0 else 0
    ticket_medio = (total_receita / total_vendas) if total_vendas > 0 else 0
    
    kpis = {
        'Impressões': total_impressoes,
        'Cliques': total_cliques,
        'Investimento': total_investimento,
        'Vendas': total_vendas,
        'Receita': total_receita,
        'CTR': ctr,
        'CPC': cpc,
        'CPA': cpa,
        'CPM': cpm,
        'ROAS': roas,
        'ACOS': acos,
        'TaxaConversao': taxa_conversao,
        'TicketMedio': ticket_medio
    }
    
    return kpis

def get_dashboard_data():
    """
    Função principal que retorna todos os dados necessários para o dashboard
    """
    df_campanhas = load_campaign_data()
    kpis = calculate_kpis(df_campanhas)
    
    return {
        'campanhas': df_campanhas,
        'kpis': kpis
    }
