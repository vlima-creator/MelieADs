"""
Código de integração das funcionalidades Engine no app.py
Inserir este código após a seção "Ações Recomendadas por Categoria" e antes de "Download Excel"

Localização no app.py: após linha ~1571 (após tab_roas)
"""

# =====================================================================
# Funcionalidades "Engine" - Smart Budget, Motor Aquecido, Filtro de Combustível
# =====================================================================

def render_engine_features(camp_strat, stock_df=None, usar_estoque=False, fmt_money_br_func=None, fmt_int_br_func=None):
    """
    Renderiza as três funcionalidades Engine no Streamlit.
    
    Parâmetros:
    -----------
    camp_strat : pd.DataFrame
        DataFrame com campanhas estratégicas
    stock_df : pd.DataFrame (opcional)
        DataFrame com dados de estoque
    usar_estoque : bool
        Indica se estoque está sendo utilizado
    fmt_money_br_func : callable
        Função para formatar valores monetários
    fmt_int_br_func : callable
        Função para formatar inteiros
    """
    import streamlit as st
    import engine_features as engine
    
    if camp_strat is None or camp_strat.empty:
        return
    
    # Usar funções padrão se não fornecidas
    if fmt_money_br_func is None:
        fmt_money_br_func = lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    if fmt_int_br_func is None:
        fmt_int_br_func = lambda x: f"{int(round(float(x))):,}".replace(",", ".")
    
    st.header("◈ Funcionalidades Engine")
    st.markdown("Ferramentas avançadas para otimizar o motor de Ads do seu negócio.")
    
    engine_tab1, engine_tab2, engine_tab3 = st.tabs([
        "◈ Smart Budget",
        "◈ Motor Aquecido",
        "◈ Filtro de Combustível"
    ])
    
    # =====================================================================
    # TAB 1: SMART BUDGET
    # =====================================================================
    with engine_tab1:
        st.subheader("◈ Smart Budget - Realocação Inteligente de Orçamento")
        st.markdown("""
        Calcula automaticamente quanto de orçamento liberar de campanhas em "Hemorragia" 
        para alocar em campanhas em "Escala". Maximiza o retorno sem aumentar o investimento total.
        """)
        
        # Executar análise de Smart Budget
        smart_budget_result = engine.calculate_smart_budget_reallocation(
            campaigns_df=camp_strat,
            hemorragia_threshold=3.0,
            escala_threshold=7.0,
            lost_budget_threshold=40.0,
            max_reallocation_pct=0.30,
            min_daily_budget=5.0
        )
        
        if smart_budget_result['reallocation_plan'].empty:
            st.info("✅ Nenhuma realocação necessária no momento. Todas as campanhas estão equilibradas.")
        else:
            summary = smart_budget_result['summary']
            
            # Métricas principais
            col1, col2, col3, col4 = st.columns(4)
            col1.metric(
                "Campanhas em Hemorragia",
                summary['total_campaigns_hemorragia'],
                delta="candidatas a liberar"
            )
            col2.metric(
                "Campanhas em Escala",
                summary['total_campaigns_escala'],
                delta="candidatas a receber"
            )
            col3.metric(
                "Orçamento Liberável",
                fmt_money_br_func(summary['total_budget_freed']),
                delta=f"{summary['coverage_pct']:.1f}% de cobertura"
            )
            col4.metric(
                "Viabilidade",
                "✅ Viável" if summary['feasible'] else "⚠️ Parcial",
                delta=f"Surplus: {fmt_money_br_func(summary['budget_surplus'])}"
            )
            
            st.divider()
            
            # Plano de realocação
            st.subheader("Plano de Realocação Recomendado")
            realloc_plan = smart_budget_result['reallocation_plan'].copy()
            realloc_plan['Orcamento_Atual'] = realloc_plan['Orcamento_Atual'].apply(fmt_money_br_func)
            realloc_plan['Valor_Recomendado'] = realloc_plan['Valor_Recomendado'].apply(fmt_money_br_func)
            realloc_plan['ROAS_Atual'] = realloc_plan['ROAS_Atual'].apply(lambda x: f"{x:.2f}x")
            st.dataframe(realloc_plan, use_container_width=True, hide_index=True)
            
            st.success(f"💡 Impacto estimado no ROAS: {summary['estimated_roas_impact']:.2f}x")
    
    # =====================================================================
    # TAB 2: ALERTA DE MOTOR AQUECIDO
    # =====================================================================
    with engine_tab2:
        st.subheader("◈ Alerta de Motor Aquecido - ROAS Excepcional")
        st.markdown("""
        Detecta automaticamente campanhas com ROAS excepcionalmente alto e sugere escala imediata.
        Essas são as oportunidades "ouro" que não devem ser perdidas.
        """)
        
        # Executar análise de Motor Aquecido
        overheated_result = engine.detect_overheated_engine_alerts(
            campaigns_df=camp_strat,
            roas_exceptional_mult=1.50,
            roas_baseline=5.0,
            min_investment=50.0,
            min_conversions=5
        )
        
        if overheated_result['alert_count'] == 0:
            st.info("✅ Nenhuma campanha com ROAS excepcional no momento. Continue monitorando!")
        else:
            # Métricas principais
            col1, col2, col3 = st.columns(3)
            col1.metric(
                "Campanhas em Alerta",
                overheated_result['alert_count'],
                delta="◈ Motor Aquecido"
            )
            col2.metric(
                "Oportunidade Total",
                fmt_money_br_func(overheated_result['total_opportunity']),
                delta="potencial com 50% mais orçamento"
            )
            col3.metric(
                "Status",
                "🚨 CRÍTICO" if any('CRITICA' in str(r) for r in overheated_result['recommendations']) else "⚠️ ALTO",
                delta="ação recomendada"
            )
            
            st.divider()
            
            # Recomendações
            st.subheader("Recomendações")
            for rec in overheated_result['recommendations']:
                st.warning(rec)
            
            st.divider()
            
            # Tabela de alertas
            st.subheader("Campanhas em Alerta")
            alerts_table = overheated_result['alerts'][[
                'Nome', 'ROAS_Real', 'Investimento', 'Receita', 'Urgencia', 'Oportunidade_Escala'
            ]].copy()
            alerts_table['ROAS_Real'] = alerts_table['ROAS_Real'].apply(lambda x: f"{x:.2f}x")
            alerts_table['Investimento'] = alerts_table['Investimento'].apply(fmt_money_br_func)
            alerts_table['Receita'] = alerts_table['Receita'].apply(fmt_money_br_func)
            alerts_table['Oportunidade_Escala'] = alerts_table['Oportunidade_Escala'].apply(fmt_money_br_func)
            st.dataframe(alerts_table, use_container_width=True, hide_index=True)
    
    # =====================================================================
    # TAB 3: FILTRO DE COMBUSTÍVEL
    # =====================================================================
    with engine_tab3:
        st.subheader("◈ Filtro de Combustível - Proteção de Estoque")
        st.markdown("""
        Monitora o consumo de estoque em tempo real e alerta antes que o "motor rode seco".
        Garante que você nunca desperdice verba em Ads sem produto para vender.
        """)
        
        # Preparar dados para análise de combustível
        fuel_stock_df = None
        if usar_estoque and stock_df is not None:
            fuel_stock_df = stock_df
        
        # Executar análise de Filtro de Combustível
        fuel_result = engine.apply_fuel_filter_logic(
            campaigns_df=camp_strat,
            stock_df=fuel_stock_df,
            estoque_critico=5,
            estoque_baixo=20,
            estoque_min_ads=10,
            burn_rate_days=7
        )
        
        summary_fuel = fuel_result['summary']
        
        # Métricas principais
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric(
            "Total de Campanhas",
            summary_fuel['total_campaigns']
        )
        col2.metric(
            "✅ OK",
            summary_fuel['campaigns_ok'],
            delta="estoque adequado"
        )
        col3.metric(
            "📦 Baixo",
            summary_fuel['campaigns_baixo'],
            delta="monitorar"
        )
        col4.metric(
            "⚠️ Crítico",
            summary_fuel['campaigns_critico'],
            delta="ação urgente"
        )
        col5.metric(
            "🛑 Vazio",
            summary_fuel['campaigns_vazio'],
            delta="pausar Ads"
        )
        
        st.divider()
        
        # Recomendações
        st.subheader("Recomendações")
        for rec in fuel_result['recommendations']:
            if "✅" in rec:
                st.success(rec)
            elif "🛑" in rec:
                st.error(rec)
            elif "⚠️" in rec or "🚨" in rec:
                st.warning(rec)
            else:
                st.info(rec)
        
        st.divider()
        
        # Tabela de status de combustível
        if not fuel_result['at_risk_campaigns'].empty:
            st.subheader("Campanhas em Risco")
            at_risk_table = fuel_result['at_risk_campaigns'][[
                'Nome', 'Estoque', 'Taxa_Consumo_Diaria', 'Dias_Estoque_Restante', 'Status_Combustivel'
            ]].copy()
            at_risk_table['Estoque'] = at_risk_table['Estoque'].apply(lambda x: f"{int(x)} un.")
            at_risk_table['Taxa_Consumo_Diaria'] = at_risk_table['Taxa_Consumo_Diaria'].apply(lambda x: f"{x:.1f} un./dia")
            at_risk_table['Dias_Estoque_Restante'] = at_risk_table['Dias_Estoque_Restante'].apply(
                lambda x: f"{x:.1f} dias" if x != float('inf') else "∞"
            )
            st.dataframe(at_risk_table, use_container_width=True, hide_index=True)
        else:
            st.success("✅ Todas as campanhas têm estoque adequado!")
