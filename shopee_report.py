"""
Módulo de Análise de Dados da Shopee
Processa relatórios CSV e calcula métricas específicas do GMV Max
"""

import pandas as pd
import numpy as np


def load_shopee_csv(file, skiprows=7):
    """
    Carrega arquivo CSV da Shopee pulando as linhas de cabeçalho
    
    Args:
        file: Arquivo uploaded via Streamlit
        skiprows: Número de linhas a pular (padrão: 7)
    
    Returns:
        DataFrame com os dados
    """
    try:
        df = pd.read_csv(file, skiprows=skiprows)
        return df
    except Exception as e:
        raise ValueError(f"Erro ao ler arquivo CSV da Shopee: {str(e)}")


def clean_shopee_data(df):
    """
    Limpa e normaliza dados da Shopee
    
    Args:
        df: DataFrame com dados brutos
    
    Returns:
        DataFrame limpo
    """
    # Remove linhas completamente vazias
    df = df.dropna(how='all')
    
    # Converte colunas numéricas
    numeric_cols = [
        'Impressões', 'Cliques', 'CTR', 'Conversões', 'Conversões Diretas',
        'Taxa de Conversão', 'Taxa de Conversão Direta',
        'Custo por Conversão', 'Custo por Conversão Direta',
        'Itens Vendidos', 'Itens Vendidos Diretos',
        'GMV', 'Receita direta', 'Despesas',
        'ROAS', 'ROAS Direto', 'ACOS', 'ACOS Direto',
        'Impressões do Produto', 'Cliques de Produtos', 'CTR do Produto'
    ]
    
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    return df


def calcular_kpis_shopee(df):
    """
    Calcula KPIs agregados da Shopee
    
    Args:
        df: DataFrame com dados limpos
    
    Returns:
        dict com KPIs
    """
    kpis = {
        "GMV Total": df['GMV'].sum() if 'GMV' in df.columns else 0,
        "Receita Direta": df['Receita direta'].sum() if 'Receita direta' in df.columns else 0,
        "Despesas": df['Despesas'].sum() if 'Despesas' in df.columns else 0,
        "Conversões": df['Conversões'].sum() if 'Conversões' in df.columns else 0,
        "Conversões Diretas": df['Conversões Diretas'].sum() if 'Conversões Diretas' in df.columns else 0,
        "Impressões": df['Impressões'].sum() if 'Impressões' in df.columns else 0,
        "Cliques": df['Cliques'].sum() if 'Cliques' in df.columns else 0,
        "Itens Vendidos": df['Itens Vendidos'].sum() if 'Itens Vendidos' in df.columns else 0,
        "Itens Vendidos Diretos": df['Itens Vendidos Diretos'].sum() if 'Itens Vendidos Diretos' in df.columns else 0,
    }
    
    # Calcula ROAS médio
    if kpis["Despesas"] > 0:
        kpis["ROAS Médio"] = kpis["GMV Total"] / kpis["Despesas"]
        kpis["ROAS Direto Médio"] = kpis["Receita Direta"] / kpis["Despesas"]
    else:
        kpis["ROAS Médio"] = 0
        kpis["ROAS Direto Médio"] = 0
    
    # Calcula CTR médio
    if kpis["Impressões"] > 0:
        kpis["CTR Médio"] = (kpis["Cliques"] / kpis["Impressões"]) * 100
    else:
        kpis["CTR Médio"] = 0
    
    # Calcula Taxa de Conversão média
    if kpis["Cliques"] > 0:
        kpis["Taxa de Conversão Média"] = (kpis["Conversões"] / kpis["Cliques"]) * 100
        kpis["Taxa de Conversão Direta Média"] = (kpis["Conversões Diretas"] / kpis["Cliques"]) * 100
    else:
        kpis["Taxa de Conversão Média"] = 0
        kpis["Taxa de Conversão Direta Média"] = 0
    
    return kpis


def calcular_credito_protecao_roas(gmv, despesas, roas_alvo, impulsao_rapida=False):
    """
    Calcula o crédito elegível da Proteção de ROAS
    
    Args:
        gmv: GMV de anúncios
        despesas: Despesas com anúncios
        roas_alvo: ROAS alvo configurado
        impulsao_rapida: Se a campanha tem Impulsão Rápida ativada
    
    Returns:
        float: Valor do crédito elegível (0 se não elegível)
    """
    if gmv <= 0 or roas_alvo <= 0:
        return 0
    
    percentual = 0.70 if impulsao_rapida else 0.90
    credito = despesas - (gmv / (roas_alvo * percentual))
    
    return max(0, credito)


def calcular_taxa_cumprimento_roas(roas_real, roas_alvo):
    """
    Calcula a taxa de cumprimento de ROAS
    
    Args:
        roas_real: ROAS real obtido
        roas_alvo: ROAS alvo configurado
    
    Returns:
        float: Taxa de cumprimento em percentual (0-100+)
    """
    if roas_alvo == 0:
        return 0
    return (roas_real / roas_alvo) * 100


def identificar_campanhas_protecao(df, roas_alvo_default=3.0):
    """
    Identifica campanhas elegíveis para Proteção de ROAS
    
    Args:
        df: DataFrame com dados de campanhas
        roas_alvo_default: ROAS alvo padrão (default: 3.0)
    
    Returns:
        DataFrame com análise de proteção
    """
    df_analise = df.copy()
    
    # Assume ROAS alvo padrão se não houver coluna específica
    if 'ROAS Alvo' not in df_analise.columns:
        df_analise['ROAS Alvo'] = roas_alvo_default
    
    # Calcula taxa de cumprimento
    df_analise['Taxa Cumprimento ROAS (%)'] = df_analise.apply(
        lambda row: calcular_taxa_cumprimento_roas(row.get('ROAS', 0), row.get('ROAS Alvo', roas_alvo_default)),
        axis=1
    )
    
    # Identifica se é elegível para proteção (taxa < 90%)
    df_analise['Elegível Proteção'] = df_analise['Taxa Cumprimento ROAS (%)'] < 90
    
    # Calcula crédito potencial (assume sem Impulsão Rápida por padrão)
    df_analise['Crédito Potencial (R$)'] = df_analise.apply(
        lambda row: calcular_credito_protecao_roas(
            row.get('GMV', 0),
            row.get('Despesas', 0),
            row.get('ROAS Alvo', roas_alvo_default),
            impulsao_rapida=False
        ),
        axis=1
    )
    
    # Status de proteção
    def definir_status_protecao(row):
        if row['Taxa Cumprimento ROAS (%)'] >= 90:
            return "✅ Não Necessita"
        elif row['Taxa Cumprimento ROAS (%)'] >= 70:
            return "⚠️ Atenção"
        else:
            return "🛡️ Elegível"
    
    df_analise['Status Proteção'] = df_analise.apply(definir_status_protecao, axis=1)
    
    return df_analise


def analisar_conversoes_diretas(df):
    """
    Analisa a relação entre conversões totais e diretas
    
    Args:
        df: DataFrame com dados de campanhas
    
    Returns:
        DataFrame com análise de conversões
    """
    df_analise = df.copy()
    
    # Calcula percentual de conversões diretas
    df_analise['% Conversões Diretas'] = df_analise.apply(
        lambda row: (row.get('Conversões Diretas', 0) / row.get('Conversões', 1) * 100) 
        if row.get('Conversões', 0) > 0 else 0,
        axis=1
    )
    
    # Classifica qualidade de atribuição
    def classificar_atribuicao(pct):
        if pct >= 80:
            return "🟢 Excelente"
        elif pct >= 60:
            return "🟡 Boa"
        elif pct >= 40:
            return "🟠 Regular"
        else:
            return "🔴 Baixa"
    
    df_analise['Qualidade Atribuição'] = df_analise['% Conversões Diretas'].apply(classificar_atribuicao)
    
    return df_analise


def gerar_recomendacoes_shopee(df, kpis):
    """
    Gera recomendações automáticas para campanhas Shopee
    
    Args:
        df: DataFrame com dados de campanhas
        kpis: Dict com KPIs agregados
    
    Returns:
        dict com listas de recomendações
    """
    recomendacoes = {
        "ativar_protecao": [],
        "otimizar_roas": [],
        "escalar_gmv": [],
        "pausar_revisar": []
    }
    
    for idx, row in df.iterrows():
        nome = row.get('Nome do Anúncio', f'Campanha {idx+1}')
        roas = row.get('ROAS', 0)
        gmv = row.get('GMV', 0)
        despesas = row.get('Despesas', 0)
        conversoes = row.get('Conversões', 0)
        
        # Ativar Proteção de ROAS
        if roas > 0 and roas < 2.5 and despesas > 50:
            recomendacoes["ativar_protecao"].append({
                "campanha": nome,
                "roas_atual": roas,
                "despesas": despesas,
                "motivo": "ROAS abaixo da meta com investimento significativo"
            })
        
        # Otimizar ROAS
        if roas > 0 and roas < 3.0 and conversoes >= 5:
            recomendacoes["otimizar_roas"].append({
                "campanha": nome,
                "roas_atual": roas,
                "conversoes": conversoes,
                "motivo": "ROAS baixo mas com volume de conversões"
            })
        
        # Escalar GMV
        if roas >= 4.0 and gmv > 0:
            recomendacoes["escalar_gmv"].append({
                "campanha": nome,
                "roas_atual": roas,
                "gmv": gmv,
                "motivo": "ROAS forte - oportunidade de escalar"
            })
        
        # Pausar/Revisar
        if despesas > 100 and (roas < 1.5 or conversoes == 0):
            recomendacoes["pausar_revisar"].append({
                "campanha": nome,
                "roas_atual": roas,
                "despesas": despesas,
                "conversoes": conversoes,
                "motivo": "Alto investimento com retorno insatisfatório"
            })
    
    return recomendacoes


def processar_relatorio_shopee(dados_gerais_file, palavras_chave_file=None):
    """
    Processa relatórios da Shopee e retorna análise completa
    
    Args:
        dados_gerais_file: Arquivo CSV de dados gerais
        palavras_chave_file: Arquivo CSV de palavras-chave (opcional)
    
    Returns:
        dict com DataFrames e análises
    """
    # Carrega dados gerais
    df_geral = load_shopee_csv(dados_gerais_file)
    df_geral = clean_shopee_data(df_geral)
    
    # Calcula KPIs
    kpis = calcular_kpis_shopee(df_geral)
    
    # Análise de proteção de ROAS
    df_protecao = identificar_campanhas_protecao(df_geral)
    
    # Análise de conversões diretas
    df_conversoes = analisar_conversoes_diretas(df_geral)
    
    # Gera recomendações
    recomendacoes = gerar_recomendacoes_shopee(df_geral, kpis)
    
    # Calcula crédito total de proteção
    credito_total = df_protecao[df_protecao['Elegível Proteção']]['Crédito Potencial (R$)'].sum()
    campanhas_protegidas = df_protecao[df_protecao['Elegível Proteção']].shape[0]
    
    kpis["Crédito Proteção Total"] = credito_total
    kpis["Campanhas com Proteção"] = campanhas_protegidas
    
    resultado = {
        "kpis": kpis,
        "df_geral": df_geral,
        "df_protecao": df_protecao,
        "df_conversoes": df_conversoes,
        "recomendacoes": recomendacoes
    }
    
    # Se houver arquivo de palavras-chave, processa também
    if palavras_chave_file is not None:
        try:
            df_keywords = load_shopee_csv(palavras_chave_file)
            df_keywords = clean_shopee_data(df_keywords)
            resultado["df_keywords"] = df_keywords
        except Exception as e:
            resultado["df_keywords"] = None
            resultado["keywords_error"] = str(e)
    
    return resultado
