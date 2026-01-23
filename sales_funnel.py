"""
Módulo para criar funil de vendas visual estilizado
Compatível com Mercado Livre e Shopee
"""

def create_sales_funnel_html(impressoes, cliques, conversoes):
    """
    Cria um funil de vendas HTML/CSS estilizado com efeito Liquid Glass
    
    Args:
        impressoes (int): Número total de impressões
        cliques (int): Número total de cliques
        conversoes (int): Número total de conversões
    
    Returns:
        str: HTML do funil de vendas
    """
    
    # Calcula taxas
    ctr = (cliques / impressoes * 100) if impressoes > 0 else 0
    cvr = (conversoes / cliques * 100) if cliques > 0 else 0
    taxa_conversao_geral = (conversoes / impressoes * 100) if impressoes > 0 else 0
    
    # Formata números
    impressoes_fmt = f"{impressoes:,.0f}".replace(",", ".")
    cliques_fmt = f"{cliques:,.0f}".replace(",", ".")
    conversoes_fmt = f"{conversoes:,.0f}".replace(",", ".")
    
    html = f"""
    <style>
        .funnel-container {{
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 0;
            padding: 2rem 1rem;
            background: linear-gradient(135deg, rgba(10, 10, 15, 0.95) 0%, rgba(20, 20, 30, 0.95) 100%);
            border-radius: 20px;
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
            margin: 1rem 0;
        }}
        
        .funnel-stage {{
            position: relative;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 120px;
            padding: 1.5rem 2rem;
            margin: -10px 0;
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.03) 100%);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 16px;
            box-shadow: 
                0 8px 32px rgba(0, 0, 0, 0.3),
                inset 0 1px 0 rgba(255, 255, 255, 0.1);
            transition: all 0.3s ease;
            z-index: 1;
        }}
        
        .funnel-stage:hover {{
            transform: translateY(-5px);
            box-shadow: 
                0 12px 40px rgba(0, 0, 0, 0.4),
                inset 0 1px 0 rgba(255, 255, 255, 0.15);
        }}
        
        .funnel-stage-top {{
            width: 90%;
            background: linear-gradient(135deg, rgba(52, 131, 250, 0.15) 0%, rgba(52, 131, 250, 0.05) 100%);
            border-color: rgba(52, 131, 250, 0.3);
        }}
        
        .funnel-stage-middle {{
            width: 70%;
            background: linear-gradient(135deg, rgba(255, 230, 0, 0.15) 0%, rgba(255, 230, 0, 0.05) 100%);
            border-color: rgba(255, 230, 0, 0.3);
        }}
        
        .funnel-stage-bottom {{
            width: 50%;
            background: linear-gradient(135deg, rgba(0, 230, 118, 0.15) 0%, rgba(0, 230, 118, 0.05) 100%);
            border-color: rgba(0, 230, 118, 0.3);
        }}
        
        .funnel-icon {{
            font-size: 2rem;
            margin-bottom: 0.5rem;
            filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
        }}
        
        .funnel-label {{
            font-size: 0.85rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            color: rgba(255, 255, 255, 0.7);
            margin-bottom: 0.5rem;
        }}
        
        .funnel-value {{
            font-size: 2rem;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 0.25rem;
            text-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
        }}
        
        .funnel-rate {{
            font-size: 0.9rem;
            color: rgba(255, 255, 255, 0.6);
            font-weight: 500;
        }}
        
        .funnel-arrow {{
            font-size: 1.5rem;
            color: rgba(255, 255, 255, 0.3);
            margin: -5px 0;
            z-index: 0;
        }}
        
        .funnel-title {{
            font-size: 1.5rem;
            font-weight: 700;
            color: #ffffff;
            text-align: center;
            margin-bottom: 1.5rem;
            text-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
        }}
        
        .funnel-summary {{
            margin-top: 1.5rem;
            padding: 1rem 2rem;
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.02) 100%);
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            text-align: center;
        }}
        
        .funnel-summary-text {{
            font-size: 0.9rem;
            color: rgba(255, 255, 255, 0.7);
            font-weight: 500;
        }}
        
        .funnel-summary-value {{
            font-size: 1.2rem;
            font-weight: 700;
            color: #ffffff;
            margin-top: 0.25rem;
        }}
    </style>
    
    <div class="funnel-container">
        <div class="funnel-title">🎯 Funil de Conversão</div>
        
        <!-- Impressões -->
        <div class="funnel-stage funnel-stage-top">
            <div class="funnel-icon">👁️</div>
            <div class="funnel-label">Impressões</div>
            <div class="funnel-value">{impressoes_fmt}</div>
            <div class="funnel-rate">Alcance total</div>
        </div>
        
        <div class="funnel-arrow">▼</div>
        
        <!-- Cliques -->
        <div class="funnel-stage funnel-stage-middle">
            <div class="funnel-icon">🖱️</div>
            <div class="funnel-label">Cliques</div>
            <div class="funnel-value">{cliques_fmt}</div>
            <div class="funnel-rate">CTR: {ctr:.2f}%</div>
        </div>
        
        <div class="funnel-arrow">▼</div>
        
        <!-- Conversões -->
        <div class="funnel-stage funnel-stage-bottom">
            <div class="funnel-icon">✅</div>
            <div class="funnel-label">Conversões</div>
            <div class="funnel-value">{conversoes_fmt}</div>
            <div class="funnel-rate">CVR: {cvr:.2f}%</div>
        </div>
        
        <!-- Resumo -->
        <div class="funnel-summary">
            <div class="funnel-summary-text">Taxa de Conversão Geral</div>
            <div class="funnel-summary-value">{taxa_conversao_geral:.3f}%</div>
        </div>
    </div>
    """
    
    return html


def create_sales_funnel_from_df(df, impressoes_col="Impressões", cliques_col="Cliques", conversoes_col="Conversões"):
    """
    Cria funil de vendas a partir de um DataFrame
    
    Args:
        df (pd.DataFrame): DataFrame com os dados
        impressoes_col (str): Nome da coluna de impressões
        cliques_col (str): Nome da coluna de cliques
        conversoes_col (str): Nome da coluna de conversões
    
    Returns:
        str: HTML do funil de vendas
    """
    
    impressoes = int(df[impressoes_col].sum()) if impressoes_col in df.columns else 0
    cliques = int(df[cliques_col].sum()) if cliques_col in df.columns else 0
    conversoes = int(df[conversoes_col].sum()) if conversoes_col in df.columns else 0
    
    return create_sales_funnel_html(impressoes, cliques, conversoes)
