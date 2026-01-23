"""
Módulo para criar funil de vendas visual minimalista
Compatível com Mercado Livre e Shopee
"""

def create_sales_funnel_html(impressoes, cliques, conversoes):
    """
    Cria um funil de vendas HTML/CSS minimalista
    
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
    
    # Calcula porcentagens relativas
    cliques_pct_initial = (cliques / impressoes * 100) if impressoes > 0 else 0
    cliques_pct_previous = 100.0  # Cliques são 100% de impressões (etapa anterior)
    
    conversoes_pct_initial = (conversoes / impressoes * 100) if impressoes > 0 else 0
    conversoes_pct_previous = (conversoes / cliques * 100) if cliques > 0 else 0
    
    # Formata números
    impressoes_fmt = f"{impressoes:,.0f}".replace(",", ".")
    cliques_fmt = f"{cliques:,.0f}".replace(",", ".")
    conversoes_fmt = f"{conversoes:,.0f}".replace(",", ".")
    
    html = f"""
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        .funnel-wrapper {{
            width: 100%;
            min-height: 500px;
            background: #0a0a0f;
            padding: 2rem;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }}
        
        .funnel-title {{
            text-align: center;
            color: #ffffff;
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 3rem;
            letter-spacing: 0.5px;
        }}
        
        .funnel-container {{
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 0;
            max-width: 1200px;
            margin: 0 auto;
            position: relative;
        }}
        
        .funnel-stage {{
            display: flex;
            align-items: center;
            justify-content: center;
            flex-direction: column;
            padding: 2rem;
            border: 2px solid rgba(255, 255, 255, 0.3);
            position: relative;
            transition: all 0.3s ease;
        }}
        
        .funnel-stage:hover {{
            border-color: rgba(255, 255, 255, 0.6);
            transform: translateY(-2px);
        }}
        
        .stage-impressoes {{
            width: 100%;
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            margin-bottom: 1.5rem;
        }}
        
        .stage-cliques {{
            width: 80%;
            background: linear-gradient(135deg, #34495e 0%, #415a77 100%);
            margin-bottom: 1.5rem;
        }}
        
        .stage-conversoes {{
            width: 60%;
            background: linear-gradient(135deg, #16a085 0%, #1abc9c 100%);
        }}
        
        .stage-label {{
            font-size: 0.85rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: rgba(255, 255, 255, 0.7);
            margin-bottom: 0.5rem;
        }}
        
        .stage-value {{
            font-size: 2rem;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 0.25rem;
        }}
        
        .stage-rate {{
            font-size: 0.9rem;
            color: rgba(255, 255, 255, 0.6);
            font-weight: 500;
        }}
        
        .connector {{
            width: 2px;
            height: 30px;
            background: repeating-linear-gradient(
                to bottom,
                rgba(255, 255, 255, 0.3) 0px,
                rgba(255, 255, 255, 0.3) 5px,
                transparent 5px,
                transparent 10px
            );
            margin: -10px 0;
        }}
        
        .stage-info {{
            position: absolute;
            right: -200px;
            top: 50%;
            transform: translateY(-50%);
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 0.75rem 1rem;
            border-radius: 4px;
            min-width: 180px;
        }}
        
        .info-row {{
            font-size: 0.75rem;
            color: rgba(255, 255, 255, 0.7);
            margin-bottom: 0.25rem;
            line-height: 1.4;
        }}
        
        .info-row:last-child {{
            margin-bottom: 0;
        }}
        
        .info-highlight {{
            color: #ffffff;
            font-weight: 600;
        }}
        
        @media (max-width: 1400px) {{
            .stage-info {{
                position: static;
                transform: none;
                margin-top: 1rem;
                margin-left: auto;
                margin-right: auto;
            }}
        }}
        
        @media (max-width: 768px) {{
            .funnel-wrapper {{
                padding: 1rem;
            }}
            
            .funnel-title {{
                font-size: 1.2rem;
                margin-bottom: 2rem;
            }}
            
            .stage-value {{
                font-size: 1.5rem;
            }}
            
            .stage-info {{
                min-width: 150px;
                padding: 0.5rem 0.75rem;
            }}
        }}
    </style>
    
    <div class="funnel-wrapper">
        <div class="funnel-title">Funil de Conversão Estratégico</div>
        
        <div class="funnel-container">
            <!-- Impressões -->
            <div class="funnel-stage stage-impressoes">
                <div class="stage-label">Impressões</div>
                <div class="stage-value">{impressoes_fmt}</div>
                <div class="stage-rate">Alcance total</div>
            </div>
            
            <div class="connector"></div>
            
            <!-- Cliques -->
            <div class="funnel-stage stage-cliques">
                <div class="stage-label">Cliques</div>
                <div class="stage-value">{cliques_fmt}</div>
                <div class="stage-rate">CTR: {ctr:.2f}%</div>
                
                <div class="stage-info">
                    <div class="info-row"><span class="info-highlight">{cliques_pct_initial:.1f}%</span> of initial</div>
                    <div class="info-row"><span class="info-highlight">{cliques_pct_previous:.1f}%</span> of previous</div>
                </div>
            </div>
            
            <div class="connector"></div>
            
            <!-- Conversões -->
            <div class="funnel-stage stage-conversoes">
                <div class="stage-label">Vendas</div>
                <div class="stage-value">{conversoes_fmt}</div>
                <div class="stage-rate">CVR: {cvr:.2f}%</div>
                
                <div class="stage-info">
                    <div class="info-row"><span class="info-highlight">{conversoes_pct_initial:.2f}%</span> of initial</div>
                    <div class="info-row"><span class="info-highlight">{conversoes_pct_previous:.1f}%</span> of previous</div>
                    <div class="info-row"><span class="info-highlight">{cvr:.2f}%</span> of total</div>
                </div>
            </div>
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
