"""
Módulo para criar funil de vendas visual com Liquid Glass
Compatível com Mercado Livre e Shopee
"""

def create_sales_funnel_html(impressoes, cliques, conversoes):
    """
    Cria um funil de vendas HTML/CSS com efeito Liquid Glass
    
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
    cliques_pct_previous = 100.0
    
    conversoes_pct_initial = (conversoes / impressoes * 100) if impressoes > 0 else 0
    conversoes_pct_previous = (conversoes / cliques * 100) if cliques > 0 else 0
    conversoes_pct_total = cvr
    
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
            min-height: 400px;
            background: linear-gradient(135deg, rgba(10, 10, 15, 0.95) 0%, rgba(20, 20, 30, 0.95) 100%);
            padding: 1.5rem;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            border-radius: 16px;
        }}
        
        .funnel-title {{
            text-align: center;
            color: #ffffff;
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 2rem;
            letter-spacing: 0.5px;
        }}
        
        .funnel-container {{
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 0;
            max-width: 900px;
            margin: 0 auto;
            position: relative;
        }}
        
        .funnel-stage {{
            display: flex;
            align-items: center;
            justify-content: center;
            flex-direction: column;
            padding: 1.25rem 1.5rem;
            position: relative;
            transition: all 0.3s ease;
            backdrop-filter: blur(20px);
            border-radius: 12px;
            box-shadow: 
                0 8px 32px rgba(0, 0, 0, 0.3),
                inset 0 1px 0 rgba(255, 255, 255, 0.1);
        }}
        
        .funnel-stage:hover {{
            transform: translateY(-3px);
            box-shadow: 
                0 12px 40px rgba(0, 0, 0, 0.4),
                inset 0 1px 0 rgba(255, 255, 255, 0.15);
        }}
        
        .stage-impressoes {{
            width: 90%;
            background: linear-gradient(135deg, rgba(52, 131, 250, 0.2) 0%, rgba(52, 131, 250, 0.1) 100%);
            border: 1px solid rgba(52, 131, 250, 0.4);
            margin-bottom: 1rem;
        }}
        
        .stage-cliques {{
            width: 75%;
            background: linear-gradient(135deg, rgba(255, 193, 7, 0.2) 0%, rgba(255, 193, 7, 0.1) 100%);
            border: 1px solid rgba(255, 193, 7, 0.4);
            margin-bottom: 1rem;
        }}
        
        .stage-conversoes {{
            width: 60%;
            background: linear-gradient(135deg, rgba(76, 175, 80, 0.2) 0%, rgba(76, 175, 80, 0.1) 100%);
            border: 1px solid rgba(76, 175, 80, 0.4);
        }}
        
        .stage-label {{
            font-size: 0.7rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            color: rgba(255, 255, 255, 0.7);
            margin-bottom: 0.4rem;
        }}
        
        .stage-value {{
            font-size: 1.75rem;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 0.2rem;
            text-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
        }}
        
        .stage-rate {{
            font-size: 0.8rem;
            color: rgba(255, 255, 255, 0.6);
            font-weight: 500;
        }}
        
        .connector {{
            width: 2px;
            height: 20px;
            background: repeating-linear-gradient(
                to bottom,
                rgba(255, 255, 255, 0.3) 0px,
                rgba(255, 255, 255, 0.3) 4px,
                transparent 4px,
                transparent 8px
            );
            margin: -5px 0;
        }}
        
        .stage-info {{
            position: absolute;
            right: -180px;
            top: 50%;
            transform: translateY(-50%);
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.03) 100%);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.15);
            padding: 0.6rem 0.9rem;
            border-radius: 8px;
            min-width: 160px;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
        }}
        
        .info-row {{
            font-size: 0.7rem;
            color: rgba(255, 255, 255, 0.7);
            margin-bottom: 0.2rem;
            line-height: 1.4;
        }}
        
        .info-row:last-child {{
            margin-bottom: 0;
        }}
        
        .info-highlight {{
            color: #ffffff;
            font-weight: 600;
        }}
        
        @media (max-width: 1200px) {{
            .stage-info {{
                position: static;
                transform: none;
                margin-top: 0.8rem;
                margin-left: auto;
                margin-right: auto;
            }}
        }}
        
        @media (max-width: 768px) {{
            .funnel-wrapper {{
                padding: 1rem;
                min-height: 350px;
            }}
            
            .funnel-title {{
                font-size: 1rem;
                margin-bottom: 1.5rem;
            }}
            
            .stage-value {{
                font-size: 1.4rem;
            }}
            
            .stage-label {{
                font-size: 0.65rem;
            }}
            
            .stage-info {{
                min-width: 140px;
                padding: 0.5rem 0.7rem;
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
                    <div class="info-row"><span class="info-highlight">{conversoes_pct_initial:.3f}%</span> of initial</div>
                    <div class="info-row"><span class="info-highlight">{conversoes_pct_previous:.2f}%</span> of previous</div>
                    <div class="info-row"><span class="info-highlight">{conversoes_pct_total:.2f}%</span> of total</div>
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
