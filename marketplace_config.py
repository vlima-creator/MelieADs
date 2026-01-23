"""
Configuração de Marketplaces
Define as características e requisitos de cada canal
"""

MARKETPLACES = {
    "mercado_livre": {
        "name": "Mercado Livre",
        "icon": "🛒",
        "color": "#ffe600",
        "reports_required": [
            {
                "key": "vendas",
                "label": "Relatório de Desempenho de Vendas (Orgânico)",
                "description": "Arquivo Excel com dados de vendas orgânicas"
            },
            {
                "key": "patrocinados",
                "label": "Relatório de Anúncios Patrocinados",
                "description": "Arquivo Excel com dados de anúncios"
            },
            {
                "key": "campanha",
                "label": "Relatório de Campanha",
                "description": "Arquivo Excel com dados de campanhas"
            }
        ],
        "reports_optional": [
            {
                "key": "estoque",
                "label": "Relatório de Estoque (Opcional)",
                "description": "Arquivo Excel com dados de estoque"
            },
            {
                "key": "snapshot",
                "label": "Snapshot de Referência (Opcional)",
                "description": "Arquivo Excel com dados históricos para comparação"
            }
        ],
        "kpis": [
            {"key": "investimento", "label": "INVESTIMENTO ADS", "icon": "💵"},
            {"key": "receita", "label": "RECEITA ADS", "icon": "💰"},
            {"key": "roas", "label": "ROAS", "icon": "📉"},
            {"key": "tacos", "label": "TACOS", "icon": "🎯"}
        ],
        "metrics": {
            "primary": "Receita Ads",
            "roas_target": 5.0,
            "tacos_target": 15.0
        }
    },
    "shopee": {
        "name": "Shopee",
        "icon": "🛍️",
        "color": "#ee4d2d",
        "reports_required": [
            {
                "key": "dados_gerais",
                "label": "Dados Gerais de Anúncios",
                "description": "Arquivo CSV com dados gerais de campanhas CPC"
            }
        ],
        "reports_optional": [
            {
                "key": "palavras_chave",
                "label": "Relatório de Palavras-chave (Opcional)",
                "description": "Arquivo CSV com dados de palavras-chave e locação"
            }
        ],
        "kpis": [
            {"key": "gmv", "label": "GMV TOTAL", "icon": "💰"},
            {"key": "despesas", "label": "DESPESAS", "icon": "💵"},
            {"key": "roas", "label": "ROAS MÉDIO", "icon": "📈"},
            {"key": "roas_direto", "label": "ROAS DIRETO", "icon": "🎯"},
            {"key": "credito_protecao", "label": "CRÉDITO PROTEÇÃO", "icon": "🛡️"},
            {"key": "campanhas_protegidas", "label": "CAMPANHAS PROTEGIDAS", "icon": "✅"}
        ],
        "metrics": {
            "primary": "GMV",
            "roas_target": 3.0,
            "protecao_roas": {
                "taxa_cumprimento_padrao": 0.90,
                "taxa_cumprimento_impulsao": 0.70,
                "conversoes_min_item_unico": 5,
                "conversoes_min_grupo": 5,
                "conversoes_min_loja": 10
            }
        }
    }
}


def get_marketplace_config(marketplace_key):
    """
    Retorna a configuração de um marketplace específico
    
    Args:
        marketplace_key: Chave do marketplace ('mercado_livre' ou 'shopee')
    
    Returns:
        dict: Configuração do marketplace
    """
    return MARKETPLACES.get(marketplace_key, None)


def get_marketplace_list():
    """
    Retorna lista de marketplaces disponíveis
    
    Returns:
        list: Lista de tuplas (key, name, icon)
    """
    return [
        (key, config["name"], config["icon"]) 
        for key, config in MARKETPLACES.items()
    ]


def get_required_reports(marketplace_key):
    """
    Retorna lista de relatórios obrigatórios para um marketplace
    
    Args:
        marketplace_key: Chave do marketplace
    
    Returns:
        list: Lista de relatórios obrigatórios
    """
    config = get_marketplace_config(marketplace_key)
    if config:
        return config.get("reports_required", [])
    return []


def get_optional_reports(marketplace_key):
    """
    Retorna lista de relatórios opcionais para um marketplace
    
    Args:
        marketplace_key: Chave do marketplace
    
    Returns:
        list: Lista de relatórios opcionais
    """
    config = get_marketplace_config(marketplace_key)
    if config:
        return config.get("reports_optional", [])
    return []


def get_kpis_config(marketplace_key):
    """
    Retorna configuração de KPIs para um marketplace
    
    Args:
        marketplace_key: Chave do marketplace
    
    Returns:
        list: Lista de KPIs configurados
    """
    config = get_marketplace_config(marketplace_key)
    if config:
        return config.get("kpis", [])
    return []
