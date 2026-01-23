"""
Função para renderizar o funil com métricas reais do relatório
"""

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
    """Renderiza um funil visual com métricas reais baseadas no relatório."""
    import pandas as pd
    
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
    
    # Calcular percentuais para a visualização do funil
    pct_cliques = (cliques / impressoes * 100) if impressoes > 0 else 0
    pct_vendas = (vendas / cliques * 100) if cliques > 0 else 0
    
    funnel_html = f"""
    <div style="
        background: linear-gradient(145deg, #141414 0%, #1a1a1a 100%);
        border-radius: 16px;
        padding: 30px;
        border: 1px solid rgba(85, 107, 47, 0.3);
        margin-top: 10px;
    ">
        <div style="text-align: center; margin-bottom: 30px;">
            <span style="color: #556B2F; font-size: 1.3rem; font-weight: 700;">FUNIL DE CONVERSÃO</span>
            <p style="color: #999999; font-size: 0.9rem; margin-top: 5px;">Visualização da jornada de compra</p>
        </div>
        
        <!-- FUNIL VISUAL -->
        <div style="display: flex; flex-direction: column; align-items: center; gap: 15px; margin-bottom: 30px;">
            
            <!-- TOPO: IMPRESSÕES -->
            <div style="
                width: 100%;
                max-width: 500px;
                background: linear-gradient(135deg, #556B2F 0%, #6B8E23 100%);
                border-radius: 12px;
                padding: 20px;
                text-align: center;
                box-shadow: 0 4px 15px rgba(85, 107, 47, 0.3);
                border: 1px solid rgba(107, 142, 35, 0.5);
            ">
                <div style="color: #ffffff; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;">
                    Impressões (Topo do Funil)
                </div>
                <div style="color: #ffffff; font-size: 2rem; font-weight: 700; font-family: 'Courier New', monospace;">
                    {fmt_int_br(impressoes)}
                </div>
                <div style="color: rgba(255,255,255,0.8); font-size: 0.8rem; margin-top: 8px;">
                    CPM: {fmt_money_br(cpm)}
                </div>
            </div>
            
            <!-- SETA PARA BAIXO -->
            <div style="color: #556B2F; font-size: 1.5rem; font-weight: 300;">↓</div>
            
            <!-- MEIO: CLIQUES -->
            <div style="
                width: 85%;
                max-width: 425px;
                background: linear-gradient(135deg, #6B8E23 0%, #556B2F 100%);
                border-radius: 12px;
                padding: 20px;
                text-align: center;
                box-shadow: 0 4px 15px rgba(85, 107, 47, 0.25);
                border: 1px solid rgba(107, 142, 35, 0.4);
            ">
                <div style="color: #ffffff; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;">
                    Cliques (Meio do Funil)
                </div>
                <div style="color: #ffffff; font-size: 2rem; font-weight: 700; font-family: 'Courier New', monospace;">
                    {fmt_int_br(cliques)}
                </div>
                <div style="color: rgba(255,255,255,0.8); font-size: 0.8rem; margin-top: 8px;">
                    CTR: {fmt_percent_br(ctr)} • CPC: {fmt_money_br(cpc)}
                </div>
            </div>
            
            <!-- SETA PARA BAIXO -->
            <div style="color: #556B2F; font-size: 1.5rem; font-weight: 300;">↓</div>
            
            <!-- FUNDO: VENDAS -->
            <div style="
                width: 70%;
                max-width: 350px;
                background: linear-gradient(135deg, #556B2F 0%, #3d4f2a 100%);
                border-radius: 12px;
                padding: 20px;
                text-align: center;
                box-shadow: 0 4px 15px rgba(85, 107, 47, 0.2);
                border: 1px solid rgba(85, 107, 47, 0.4);
            ">
                <div style="color: #ffffff; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;">
                    Vendas (Fundo do Funil)
                </div>
                <div style="color: #ffffff; font-size: 2rem; font-weight: 700; font-family: 'Courier New', monospace;">
                    {fmt_int_br(vendas)}
                </div>
                <div style="color: rgba(255,255,255,0.8); font-size: 0.8rem; margin-top: 8px;">
                    Taxa: {fmt_percent_br(taxa_conversao)} • CPA: {fmt_money_br(cpa)}
                </div>
            </div>
        </div>
        
        <!-- MÉTRICAS DE EFICIÊNCIA -->
        <div style="
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid rgba(85, 107, 47, 0.3);
        ">
            <div style="
                background: rgba(85, 107, 47, 0.15);
                border-left: 3px solid #556B2F;
                border-radius: 8px;
                padding: 15px;
                text-align: center;
            ">
                <div style="color: #999999; font-size: 0.8rem; text-transform: uppercase; font-weight: 600; margin-bottom: 8px;">ROAS</div>
                <div style="color: #ffffff; font-size: 1.8rem; font-weight: 700; font-family: 'Courier New', monospace;">
                    {fmt_number_br(roas, 2)}x
                </div>
                <div style="color: #999999; font-size: 0.75rem; margin-top: 5px;">Retorno sobre Investimento</div>
            </div>
            
            <div style="
                background: rgba(85, 107, 47, 0.15);
                border-left: 3px solid #6B8E23;
                border-radius: 8px;
                padding: 15px;
                text-align: center;
            ">
                <div style="color: #999999; font-size: 0.8rem; text-transform: uppercase; font-weight: 600; margin-bottom: 8px;">RECEITA TOTAL</div>
                <div style="color: #ffffff; font-size: 1.8rem; font-weight: 700; font-family: 'Courier New', monospace;">
                    {fmt_money_br(receita)}
                </div>
                <div style="color: #999999; font-size: 0.75rem; margin-top: 5px;">GMV Gerado</div>
            </div>
            
            <div style="
                background: rgba(85, 107, 47, 0.15);
                border-left: 3px solid #556B2F;
                border-radius: 8px;
                padding: 15px;
                text-align: center;
            ">
                <div style="color: #999999; font-size: 0.8rem; text-transform: uppercase; font-weight: 600; margin-bottom: 8px;">INVESTIMENTO</div>
                <div style="color: #ffffff; font-size: 1.8rem; font-weight: 700; font-family: 'Courier New', monospace;">
                    {fmt_money_br(investimento)}
                </div>
                <div style="color: #999999; font-size: 0.75rem; margin-top: 5px;">Total Gasto</div>
            </div>
            
            <div style="
                background: rgba(85, 107, 47, 0.15);
                border-left: 3px solid #6B8E23;
                border-radius: 8px;
                padding: 15px;
                text-align: center;
            ">
                <div style="color: #999999; font-size: 0.8rem; text-transform: uppercase; font-weight: 600; margin-bottom: 8px;">TICKET MÉDIO</div>
                <div style="color: #ffffff; font-size: 1.8rem; font-weight: 700; font-family: 'Courier New', monospace;">
                    {fmt_money_br(ticket_medio)}
                </div>
                <div style="color: #999999; font-size: 0.75rem; margin-top: 5px;">Valor Médio por Venda</div>
            </div>
        </div>
    </div>
    """
    return funnel_html
