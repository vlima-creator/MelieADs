"""
Módulo de Funcionalidades "Engine" para AdsEngine
Implementa as três peças principais do motor:
1. Smart Budget: Calculadora de realocação de orçamento
2. Alerta de Motor Aquecido: Notificações de ROAS excepcional
3. Filtro de Combustível: Lógica de estoque aprimorada
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional


# =====================================================================
# 1. SMART BUDGET - Calculadora de Realocação de Orçamento
# =====================================================================

def calculate_smart_budget_reallocation(
    campaigns_df: pd.DataFrame,
    hemorragia_threshold: float = 3.0,
    escala_threshold: float = 7.0,
    lost_budget_threshold: float = 40.0,
    max_reallocation_pct: float = 0.30,
    min_daily_budget: float = 5.0,
) -> Dict:
    """
    Calcula a realocação inteligente de orçamento de campanhas em "Hemorragia"
    para campanhas em "Escala".
    
    Parâmetros:
    -----------
    campaigns_df : pd.DataFrame
        DataFrame com colunas: Nome, ROAS_Real, Investimento, Orçamento, 
        Perdidas_Orc, Quadrante
    hemorragia_threshold : float
        ROAS máximo para considerar uma campanha em hemorragia (default: 3.0)
    escala_threshold : float
        ROAS mínimo para considerar uma campanha em escala (default: 7.0)
    lost_budget_threshold : float
        % mínima de perda por orçamento para escala (default: 40.0)
    max_reallocation_pct : float
        Máximo de orçamento a realocar de uma campanha (default: 30%)
    min_daily_budget : float
        Orçamento diário mínimo após realocação (default: R$ 5.00)
    
    Retorna:
    --------
    Dict com:
        - 'reallocation_plan': DataFrame com plano de realocação
        - 'total_budget_freed': float com total liberado
        - 'total_budget_needed': float com total necessário
        - 'feasible': bool indicando se a realocação é viável
        - 'summary': Dict com resumo executivo
    """
    
    if campaigns_df is None or campaigns_df.empty:
        return {
            'reallocation_plan': pd.DataFrame(),
            'total_budget_freed': 0.0,
            'total_budget_needed': 0.0,
            'feasible': False,
            'summary': {}
        }
    
    df = campaigns_df.copy()
    
    # Garantir colunas numéricas
    numeric_cols = ['ROAS_Real', 'Investimento', 'Orçamento', 'Perdidas_Orc']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Identificar campanhas em hemorragia (candidatas a liberar orçamento)
    hemorragia = df[
        (df['ROAS_Real'] < hemorragia_threshold) & 
        (df['Investimento'] > 0)
    ].copy()
    
    # Identificar campanhas em escala (candidatas a receber orçamento)
    escala = df[
        (df['ROAS_Real'] >= escala_threshold) & 
        (df['Perdidas_Orc'] >= lost_budget_threshold) &
        (df['Investimento'] > 0)
    ].copy()
    
    # Calcular orçamento disponível para realocação
    hemorragia['Budget_Liberavel'] = hemorragia['Orçamento'].apply(
        lambda x: max(0, x * max_reallocation_pct)
    )
    hemorragia['Budget_Minimo'] = min_daily_budget
    hemorragia['Budget_Disponivel'] = hemorragia['Budget_Liberavel']
    
    total_budget_freed = hemorragia['Budget_Disponivel'].sum()
    
    # Calcular orçamento necessário para campanhas em escala
    escala['Budget_Necessario'] = escala['Orçamento'].apply(
        lambda x: x * 0.50  # Aumento de 50% no orçamento
    )
    
    total_budget_needed = escala['Budget_Necessario'].sum()
    
    # Construir plano de realocação
    reallocation_plan = pd.DataFrame({
        'Tipo': ['Hemorragia'] * len(hemorragia) + ['Escala'] * len(escala),
        'Campanha': list(hemorragia.get('Nome', [])) + list(escala.get('Nome', [])),
        'ROAS_Atual': list(hemorragia.get('ROAS_Real', [])) + list(escala.get('ROAS_Real', [])),
        'Orcamento_Atual': list(hemorragia.get('Orçamento', [])) + list(escala.get('Orçamento', [])),
        'Acao': (
            ['Liberar'] * len(hemorragia) + 
            ['Aumentar'] * len(escala)
        ),
        'Valor_Recomendado': list(hemorragia.get('Budget_Disponivel', [])) + list(escala.get('Budget_Necessario', []))
    })
    
    # Calcular viabilidade
    feasible = total_budget_freed >= (total_budget_needed * 0.80)  # 80% de cobertura
    
    # Resumo executivo
    summary = {
        'total_campaigns_hemorragia': len(hemorragia),
        'total_campaigns_escala': len(escala),
        'total_budget_freed': round(total_budget_freed, 2),
        'total_budget_needed': round(total_budget_needed, 2),
        'budget_surplus': round(total_budget_freed - total_budget_needed, 2),
        'feasible': feasible,
        'coverage_pct': round((total_budget_freed / max(total_budget_needed, 1)) * 100, 1),
        'estimated_roas_impact': _estimate_roas_impact(escala, total_budget_needed)
    }
    
    return {
        'reallocation_plan': reallocation_plan,
        'total_budget_freed': total_budget_freed,
        'total_budget_needed': total_budget_needed,
        'feasible': feasible,
        'summary': summary
    }


def _estimate_roas_impact(escala_df: pd.DataFrame, additional_budget: float) -> float:
    """Estima o impacto no ROAS com orçamento adicional."""
    if escala_df.empty or additional_budget <= 0:
        return 0.0
    
    try:
        current_roas = escala_df['ROAS_Real'].mean()
        # Estimativa conservadora: 5% de melhoria a cada 50% de aumento de orçamento
        improvement_factor = 1.05
        return round(current_roas * improvement_factor, 2)
    except Exception:
        return 0.0


# =====================================================================
# 2. ALERTA DE MOTOR AQUECIDO - Notificações de ROAS Excepcional
# =====================================================================

def detect_overheated_engine_alerts(
    campaigns_df: pd.DataFrame,
    roas_exceptional_mult: float = 1.50,
    roas_baseline: float = 5.0,
    min_investment: float = 50.0,
    min_conversions: int = 5,
) -> Dict:
    """
    Detecta campanhas com ROAS excepcionalmente alto e sugere escala imediata.
    
    Parâmetros:
    -----------
    campaigns_df : pd.DataFrame
        DataFrame com colunas: Nome, ROAS_Real, Investimento, Vendas, Receita
    roas_exceptional_mult : float
        Multiplicador do ROAS baseline para considerar excepcional (default: 1.50x)
    roas_baseline : float
        ROAS baseline da conta (default: 5.0)
    min_investment : float
        Investimento mínimo para gerar alerta (default: R$ 50.00)
    min_conversions : int
        Mínimo de conversões para validar o alerta (default: 5)
    
    Retorna:
    --------
    Dict com:
        - 'alerts': DataFrame com campanhas em alerta
        - 'alert_count': int com número de alertas
        - 'total_opportunity': float com oportunidade total em R$
        - 'recommendations': List com recomendações
    """
    
    if campaigns_df is None or campaigns_df.empty:
        return {
            'alerts': pd.DataFrame(),
            'alert_count': 0,
            'total_opportunity': 0.0,
            'recommendations': []
        }
    
    df = campaigns_df.copy()
    
    # Garantir colunas numéricas
    numeric_cols = ['ROAS_Real', 'Investimento', 'Vendas', 'Receita']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Calcular threshold de ROAS excepcional
    roas_threshold = roas_baseline * roas_exceptional_mult
    
    # Identificar campanhas com ROAS excepcional
    alerts = df[
        (df['ROAS_Real'] >= roas_threshold) &
        (df['Investimento'] >= min_investment) &
        (df['Vendas'] >= min_conversions)
    ].copy()
    
    if not alerts.empty:
        # Calcular oportunidade de escala
        alerts['Oportunidade_Escala'] = alerts.apply(
            lambda r: _calculate_scale_opportunity(
                r.get('Receita', 0),
                r.get('Investimento', 0),
                r.get('ROAS_Real', 0)
            ),
            axis=1
        )
        
        alerts['Urgencia'] = alerts['ROAS_Real'].apply(
            lambda x: 'CRITICA' if x >= roas_threshold * 1.5 else 'ALTA'
        )
        
        alerts['Status_Motor'] = '🔥 AQUECIDO'
    
    total_opportunity = alerts['Oportunidade_Escala'].sum() if not alerts.empty else 0.0
    
    # Gerar recomendações
    recommendations = _generate_overheated_recommendations(alerts, roas_threshold)
    
    return {
        'alerts': alerts,
        'alert_count': len(alerts),
        'total_opportunity': round(total_opportunity, 2),
        'recommendations': recommendations
    }


def _calculate_scale_opportunity(receita: float, investimento: float, roas: float) -> float:
    """Calcula oportunidade de escala com aumento de 50% no investimento."""
    try:
        if investimento > 0 and roas > 0:
            additional_investment = investimento * 0.50
            potential_revenue = additional_investment * roas
            return potential_revenue
    except Exception:
        pass
    return 0.0


def _generate_overheated_recommendations(alerts_df: pd.DataFrame, roas_threshold: float) -> List[str]:
    """Gera recomendações baseadas em alertas de motor aquecido."""
    recommendations = []
    
    if alerts_df.empty:
        return recommendations
    
    alert_count = len(alerts_df)
    total_opportunity = alerts_df['Oportunidade_Escala'].sum()
    
    if alert_count > 0:
        recommendations.append(
            f"🚀 {alert_count} campanha(s) com ROAS excepcional detectada(s). "
            f"Oportunidade total: R$ {total_opportunity:,.2f}"
        )
    
    critical_alerts = len(alerts_df[alerts_df['Urgencia'] == 'CRITICA'])
    if critical_alerts > 0:
        recommendations.append(
            f"⚠️ {critical_alerts} campanha(s) com ROAS CRÍTICO (>150% do baseline). "
            f"Recomenda-se escala imediata!"
        )
    
    high_roas = alerts_df[alerts_df['ROAS_Real'] >= roas_threshold * 1.2]
    if not high_roas.empty:
        top_campaign = high_roas.loc[high_roas['ROAS_Real'].idxmax()]
        recommendations.append(
            f"💡 Campanha destaque: {top_campaign.get('Nome', 'N/A')} com ROAS {top_campaign.get('ROAS_Real', 0):.2f}x. "
            f"Considere aumentar orçamento em 50-100%."
        )
    
    return recommendations


# =====================================================================
# 3. FILTRO DE COMBUSTÍVEL - Lógica de Estoque Aprimorada
# =====================================================================

def apply_fuel_filter_logic(
    campaigns_df: pd.DataFrame,
    stock_df: Optional[pd.DataFrame] = None,
    estoque_critico: int = 5,
    estoque_baixo: int = 20,
    estoque_min_ads: int = 10,
    burn_rate_days: int = 7,
) -> Dict:
    """
    Aplica lógica avançada de estoque ("Filtro de Combustível") para garantir
    que o motor nunca rode "seco" (sem produto).
    
    Parâmetros:
    -----------
    campaigns_df : pd.DataFrame
        DataFrame com colunas: Nome, Vendas, Investimento, Quadrante, Estoque
    stock_df : pd.DataFrame (opcional)
        DataFrame com colunas: MLB_key, SKU_key, Estoque
    estoque_critico : int
        Nível crítico de estoque (default: 5 unidades)
    estoque_baixo : int
        Nível baixo de estoque (default: 20 unidades)
    estoque_min_ads : int
        Estoque mínimo para ativar Ads (default: 10 unidades)
    burn_rate_days : int
        Dias para calcular taxa de consumo (default: 7 dias)
    
    Retorna:
    --------
    Dict com:
        - 'fuel_status': DataFrame com status de combustível
        - 'at_risk_campaigns': DataFrame com campanhas em risco
        - 'recommendations': List com recomendações
        - 'summary': Dict com resumo
    """
    
    if campaigns_df is None or campaigns_df.empty:
        return {
            'fuel_status': pd.DataFrame(),
            'at_risk_campaigns': pd.DataFrame(),
            'recommendations': [],
            'summary': {}
        }
    
    df = campaigns_df.copy()
    
    # Garantir que a coluna Estoque exista para evitar erro de chave
    if 'Estoque' not in df.columns:
        df['Estoque'] = 0
    
    # Garantir colunas numéricas
    numeric_cols = ['Vendas', 'Investimento', 'Estoque']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Merge com dados de estoque se fornecido
    if stock_df is not None and not stock_df.empty:
        # Verificar se há colunas de chave para merge
        merge_keys = [k for k in ['MLB_key', 'SKU_key'] if k in df.columns and k in stock_df.columns]
        if merge_keys:
            df = df.merge(stock_df, how='left', on=merge_keys, suffixes=('', '_stock'))
            # Usar valor do merge se disponível
            if 'Estoque_stock' in df.columns:
                df['Estoque'] = df['Estoque_stock'].fillna(df['Estoque'])
    
    # Calcular taxa de consumo (burn rate)
    df['Taxa_Consumo_Diaria'] = df['Vendas'].apply(
        lambda x: x / burn_rate_days if x > 0 else 0
    )
    
    # Calcular dias de estoque restantes
    df['Dias_Estoque_Restante'] = df.apply(
        lambda r: (
            r.get('Estoque', 0) / max(r.get('Taxa_Consumo_Diaria', 0), 0.1)
            if r.get('Taxa_Consumo_Diaria', 0) > 0 else float('inf')
        ),
        axis=1
    )
    
    # Classificar status de combustível
    df['Status_Combustivel'] = df.apply(
        lambda r: _classify_fuel_status(
            r.get('Estoque', 0),
            r.get('Dias_Estoque_Restante', 0),
            estoque_critico,
            estoque_baixo,
            estoque_min_ads
        ),
        axis=1
    )
    
    # Identificar campanhas em risco
    at_risk = df[
        (df['Status_Combustivel'].isin(['CRITICO', 'VAZIO'])) |
        (df['Dias_Estoque_Restante'] < 3)
    ].copy()
    
    # Gerar recomendações
    recommendations = _generate_fuel_recommendations(df, at_risk, estoque_critico)
    
    # Resumo
    summary = {
        'total_campaigns': len(df),
        'campaigns_ok': len(df[df['Status_Combustivel'] == 'OK']),
        'campaigns_baixo': len(df[df['Status_Combustivel'] == 'BAIXO']),
        'campaigns_critico': len(df[df['Status_Combustivel'] == 'CRITICO']),
        'campaigns_vazio': len(df[df['Status_Combustivel'] == 'VAZIO']),
        'total_estoque': int(df['Estoque'].sum()),
        'at_risk_count': len(at_risk),
        'average_dias_restante': round(df['Dias_Estoque_Restante'].replace([np.inf, -np.inf], 0).mean(), 1)
    }
    
    return {
        'fuel_status': df,
        'at_risk_campaigns': at_risk,
        'recommendations': recommendations,
        'summary': summary
    }


def _classify_fuel_status(
    estoque: float,
    dias_restante: float,
    critico: int,
    baixo: int,
    min_ads: int
) -> str:
    """Classifica o status de combustível de uma campanha."""
    
    if estoque <= 0:
        return 'VAZIO'
    if estoque < critico or dias_restante < 1:
        return 'CRITICO'
    if estoque < baixo or dias_restante < 3:
        return 'BAIXO'
    if estoque < min_ads:
        return 'INSUFICIENTE_ADS'
    
    return 'OK'


def _generate_fuel_recommendations(
    campaigns_df: pd.DataFrame,
    at_risk_df: pd.DataFrame,
    critico_threshold: int
) -> List[str]:
    """Gera recomendações baseadas no status de combustível."""
    recommendations = []
    
    if at_risk_df.empty:
        recommendations.append("✅ Todos os produtos têm estoque adequado. Motor rodando normalmente.")
        return recommendations
    
    vazio_count = len(at_risk_df[at_risk_df['Status_Combustivel'] == 'VAZIO'])
    if vazio_count > 0:
        recommendations.append(
            f"🛑 {vazio_count} produto(s) COM ESTOQUE ZERADO! "
            f"Pausar Ads imediatamente para evitar desperdício."
        )
    
    critico_count = len(at_risk_df[at_risk_df['Status_Combustivel'] == 'CRITICO'])
    if critico_count > 0:
        recommendations.append(
            f"⚠️ {critico_count} produto(s) em nível CRÍTICO (<{critico_threshold} unidades). "
            f"Recomenda-se pausar Ads ou reduzir orçamento em 50%."
        )
    
    baixo_count = len(at_risk_df[at_risk_df['Status_Combustivel'] == 'BAIXO'])
    if baixo_count > 0:
        recommendations.append(
            f"📦 {baixo_count} produto(s) com estoque BAIXO. "
            f"Monitore de perto e considere reduzir lances."
        )
    
    # Produtos com menos de 3 dias de estoque
    urgente = at_risk_df[at_risk_df['Dias_Estoque_Restante'] < 3]
    if not urgente.empty:
        top_urgente = urgente.loc[urgente['Dias_Estoque_Restante'].idxmin()]
        recommendations.append(
            f"🚨 URGENTE: {top_urgente.get('Nome', 'Produto')} acaba em "
            f"{top_urgente.get('Dias_Estoque_Restante', 0):.1f} dias. "
            f"Reposição necessária!"
        )
    
    return recommendations


# =====================================================================
# Função Auxiliar: Integração Completa
# =====================================================================

def run_engine_diagnostics(
    campaigns_df: pd.DataFrame,
    stock_df: Optional[pd.DataFrame] = None,
    **kwargs
) -> Dict:
    """
    Executa diagnóstico completo do "Engine" com as três funcionalidades.
    
    Retorna um relatório consolidado com Smart Budget, Alertas de Motor Aquecido
    e Filtro de Combustível.
    """
    
    diagnostics = {
        'smart_budget': calculate_smart_budget_reallocation(campaigns_df, **{
            k: v for k, v in kwargs.items() 
            if k.startswith('budget_') or k in ['hemorragia_threshold', 'escala_threshold', 'lost_budget_threshold', 'max_reallocation_pct', 'min_daily_budget']
        }),
        'overheated_alerts': detect_overheated_engine_alerts(campaigns_df, **{
            k: v for k, v in kwargs.items() 
            if k.startswith('roas_') or k in ['min_investment', 'min_conversions', 'roas_exceptional_mult', 'roas_baseline']
        }),
        'fuel_filter': apply_fuel_filter_logic(campaigns_df, stock_df, **{
            k: v for k, v in kwargs.items() 
            if k.startswith('estoque_') or k in ['burn_rate_days']
        })
    }
    
    return diagnostics
