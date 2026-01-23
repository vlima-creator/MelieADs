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
    """Renderiza um funil com métricas reais baseadas no relatório."""
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
    
    funnel_html = f"""
    <div style="
        background: linear-gradient(145deg, #141414 0%, #1a1a1a 100%);
        border-radius: 16px;
        padding: 25px;
        border: 1px solid rgba(85, 107, 47, 0.3);
        margin-top: 10px;
    ">
        <div style="text-align: center; margin-bottom: 20px;">
            <span style="color: #556B2F; font-size: 1.1rem; font-weight: 600;">⏬ Funil de Campanhas</span>
        </div>
        
        <!-- TOPO DO FUNIL: AWARENESS/ATRAÇÃO -->
        <div style="margin-bottom: 20px; padding: 15px; background: rgba(85, 107, 47, 0.1); border-left: 3px solid #556B2F; border-radius: 8px;">
            <div style="color: #556B2F; font-weight: 600; margin-bottom: 10px; font-size: 0.95rem;">🎯 TOPO DO FUNIL (Awareness/Atração)</div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 0.85rem;">
                <div style="color: #cccccc;">Impressões: <span style="color: #ffffff; font-weight: 600;">{fmt_int_br(impressoes)}</span></div>
                <div style="color: #cccccc;">CTR: <span style="color: #ffffff; font-weight: 600;">{fmt_percent_br(ctr)}</span></div>
                <div style="color: #cccccc;">CPM: <span style="color: #ffffff; font-weight: 600;">{fmt_money_br(cpm)}</span></div>
            </div>
        </div>
        
        <!-- MEIO DO FUNIL: CONSIDERAÇÃO/INTENÇÃO -->
        <div style="margin-bottom: 20px; padding: 15px; background: rgba(85, 107, 47, 0.15); border-left: 3px solid #6B8E23; border-radius: 8px;">
            <div style="color: #6B8E23; font-weight: 600; margin-bottom: 10px; font-size: 0.95rem;">🎯 MEIO DO FUNIL (Consideração/Intenção)</div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 0.85rem;">
                <div style="color: #cccccc;">Cliques: <span style="color: #ffffff; font-weight: 600;">{fmt_int_br(cliques)}</span></div>
                <div style="color: #cccccc;">CPC: <span style="color: #ffffff; font-weight: 600;">{fmt_money_br(cpc)}</span></div>
            </div>
        </div>
        
        <!-- FUNDO DO FUNIL: DECISÃO/CONVERSÃO -->
        <div style="margin-bottom: 20px; padding: 15px; background: rgba(85, 107, 47, 0.2); border-left: 3px solid #808000; border-radius: 8px;">
            <div style="color: #808000; font-weight: 600; margin-bottom: 10px; font-size: 0.95rem;">🎯 FUNDO DO FUNIL (Decisão/Conversão)</div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 0.85rem;">
                <div style="color: #cccccc;">Vendas: <span style="color: #ffffff; font-weight: 600;">{fmt_int_br(vendas)}</span></div>
                <div style="color: #cccccc;">Taxa Conversão: <span style="color: #ffffff; font-weight: 600;">{fmt_percent_br(taxa_conversao)}</span></div>
                <div style="color: #cccccc;">Receita: <span style="color: #ffffff; font-weight: 600;">{fmt_money_br(receita)}</span></div>
                <div style="color: #cccccc;">CPA: <span style="color: #ffffff; font-weight: 600;">{fmt_money_br(cpa)}</span></div>
            </div>
        </div>
        
        <!-- EFICIÊNCIA E RENTABILIDADE -->
        <div style="padding: 15px; background: rgba(85, 107, 47, 0.25); border-left: 3px solid #556B2F; border-radius: 8px;">
            <div style="color: #556B2F; font-weight: 600; margin-bottom: 10px; font-size: 0.95rem;">💰 EFICIÊNCIA E RENTABILIDADE</div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 0.85rem;">
                <div style="color: #cccccc;">ROAS: <span style="color: #ffffff; font-weight: 600;">{fmt_number_br(roas, 2)}x</span></div>
                <div style="color: #cccccc;">ACOS: <span style="color: #ffffff; font-weight: 600;">{fmt_percent_br(tacos * 100 if tacos < 2 else tacos)}</span></div>
                <div style="color: #cccccc;">Investimento: <span style="color: #ffffff; font-weight: 600;">{fmt_money_br(investimento)}</span></div>
                <div style="color: #cccccc;">Ticket Médio: <span style="color: #ffffff; font-weight: 600;">{fmt_money_br(ticket_medio)}</span></div>
            </div>
        </div>
    </div>
    """
    return funnel_html
