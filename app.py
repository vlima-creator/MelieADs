#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aplicação Streamlit - Tamanho do Mercado
Dashboard interativo para análise estratégica de múltiplas categorias macro
Layout Modernizado - Versão Dark Theme
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import sys
import os
import json
import re
import io
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))
from utils.pdf_generator import PDFReportGenerator

from utils.market_analyzer import MarketAnalyzer
from utils.visualizations import (
    criar_grafico_evolucao_categoria,
    criar_grafico_ticket_medio,
    criar_grafico_ranking_subcategorias,
    criar_grafico_mercado_subcategorias,
    criar_grafico_cenarios,
    criar_grafico_crescimento,
    criar_gauge_score,
    criar_comparacao_tickets
)

# Configuração da página
st.set_page_config(
    page_title="Inteligência de Mercado",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- FUNÇÕES UTILITÁRIAS ---

def format_br(valor):
    """Formata números para o padrão brasileiro (1.234,56)"""
    if valor is None: return "0,00"
    try:
        return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return str(valor)

def parse_large_number(text):
    """Converte strings como '1.5M' ou '500k' em números reais"""
    if isinstance(text, (int, float)):
        return float(text)
    
    text = str(text).strip().upper()
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        text = text.replace(",", ".")
    
    multipliers = {'K': 1_000, 'M': 1_000_000, 'B': 1_000_000_000}
    match = re.match(r"([\d.]+)([KMB]?)", text)
    if match:
        value, unit = match.groups()
        try:
            num = float(value)
            if unit in multipliers:
                num *= multipliers[unit]
            return num
        except ValueError:
            return 0.0
    return 0.0

def safe_float(val):
    try:
        if pd.isna(val): return 0.0
        return float(val)
    except:
        return 0.0

def calcular_limites_ticket_local(ticket_mercado, range_permitido=0.20):
    """Calcula limites inferior e superior baseado no ticket do mercado"""
    if not ticket_mercado: return 0.0, 0.0
    inf = ticket_mercado * (1 - range_permitido)
    sup = ticket_mercado * (1 + range_permitido)
    return inf, sup

def criar_metric_card(icon_svg, label, value, border_color="#1E3A8A"):
    """Cria um card de métrica estilizado com ícone circular"""
    return f"""
    <div style="
        background: #0a0a0a;
        border: 1px solid #1a1a1a;
        border-radius: 16px;
        padding: 24px 20px;
        text-align: left;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    ">
        <div style="
            width: 45px;
            height: 45px;
            background: #1a1a1a;
            border: 1px solid #333;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 20px;
        ">
            {icon_svg}
        </div>
        <div>
            <div style="
                font-size: 0.7rem;
                color: #FFFFFF;
                text-transform: uppercase;
                letter-spacing: 1.5px;
                margin-bottom: 8px;
                font-weight: 600;
                opacity: 0.8;
            ">{label}</div>
            <div style="
                font-size: 1.5rem;
                color: #FFFFFF;
                font-weight: 700;
            ">{value}</div>
        </div>
    </div>
    """

# Ícones SVG Estilizados
SVG_ICONS = {
    "box": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"></path><path d="m3.3 7 8.7 5 8.7-5"></path><path d="M12 22V12"></path></svg>',
    "dollar": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="1" x2="12" y2="23"></line><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>',
    "chart": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>',
    "target": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><circle cx="12" cy="12" r="6"></circle><circle cx="12" cy="12" r="2"></circle></svg>',
    "user": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>',
    "file": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>'
}

# --- INICIALIZAÇÃO ---

# Garantir que o analyzer esteja sempre na sessão e atualizado
if 'analyzer' not in st.session_state:
    st.session_state.analyzer = MarketAnalyzer()
else:
    # Verificar se o analyzer na sessão tem os métodos mais recentes
    # Se não tiver, migramos os dados para uma nova instância da classe atualizada
    if not hasattr(st.session_state.analyzer, 'identificar_anomalias') or not hasattr(st.session_state.analyzer, 'editar_mercado_categoria'):
        old_data = st.session_state.analyzer
        new_analyzer = MarketAnalyzer()
        # Migração segura de dados
        new_analyzer.cliente_data = getattr(old_data, 'cliente_data', {})
        new_analyzer.mercado_categoria = getattr(old_data, 'mercado_categoria', {})
        new_analyzer.mercado_subcategorias = getattr(old_data, 'mercado_subcategorias', {})
        st.session_state.analyzer = new_analyzer
        st.toast("🔄 Sistema atualizado para a versão de Inteligência 2.0", icon="🚀")

# --- LÓGICA DE IMPORTAÇÃO EXCEL ---

def processar_excel(file):
    try:
        temp_analyzer = MarketAnalyzer()
        
        # 1. Cliente
        df_cliente = pd.read_excel(file, sheet_name="Cliente", header=None)
        
        def get_val_by_label(labels, default=""):
            if isinstance(labels, str): labels = [labels]
            for i in range(len(df_cliente)):
                cell_val = str(df_cliente.iloc[i, 0]).strip().lower()
                for label in labels:
                    if label.lower() in cell_val:
                        return df_cliente.iloc[i, 1]
            return default

        empresa = str(get_val_by_label(["Empresa", "Nome"], "Empresa Exemplo"))
        cat_macro_cliente = str(get_val_by_label(["Categoria Macro", "Macro", "Categoria"], "Geral"))
        ticket_medio = safe_float(get_val_by_label(["Ticket Médio Geral", "Ticket Médio"], 0))
        margem = safe_float(get_val_by_label(["Margem Atual", "Margem"], 0))
        fat_3m = safe_float(get_val_by_label(["Faturamento Médio 3M", "Faturamento"], 0))
        uni_3m = int(safe_float(get_val_by_label(["Unidades Médias 3M", "Unidades"], 0)))
        range_p = safe_float(get_val_by_label(["Range Permitido", "Range"], 0.20))
        ticket_c = get_val_by_label(["Ticket Customizado", "Customizado"], None)
        ticket_custom = safe_float(ticket_c) if pd.notna(ticket_c) and str(ticket_c).strip() != "" else None
        
        temp_analyzer.set_cliente_data(
            empresa=empresa, categoria=cat_macro_cliente, ticket_medio=ticket_medio,
            margem=margem, faturamento_3m=fat_3m, unidades_3m=uni_3m,
            range_permitido=range_p, ticket_custom=ticket_custom
        )
        
        # 2. Mercado Categoria
        df_cat = pd.read_excel(file, sheet_name="Mercado_Categoria", skiprows=2)
        
        def find_col(df, possible_names):
            for col in df.columns:
                if any(name.lower() in str(col).lower() for name in possible_names):
                    return col
            return None

        col_cat = find_col(df_cat, ["Categoria"])
        col_per = find_col(df_cat, ["Periodo", "Período"])
        col_fat = find_col(df_cat, ["Faturamento"])
        col_uni = find_col(df_cat, ["Unidades"])

        count_cat = 0
        if col_cat and col_per:
            for _, row in df_cat.iterrows():
                if pd.notna(row[col_cat]) and pd.notna(row[col_per]):
                    temp_analyzer.add_mercado_categoria(
                        str(row[col_cat]), str(row[col_per]), 
                        safe_float(row[col_fat]) if col_fat and col_fat in row and pd.notna(row[col_fat]) else 0, 
                        int(safe_float(row[col_uni])) if col_uni and col_uni in row and pd.notna(row[col_uni]) else 0
                    )
                    count_cat += 1
                
        # 3. Mercado Subcategoria
        df_sub = pd.read_excel(file, sheet_name="Mercado_Subcategoria", skiprows=2)
        
        col_sub_cat = find_col(df_sub, ["Categoria"])
        col_sub_name = find_col(df_sub, ["Subcategoria"])
        col_sub_fat = find_col(df_sub, ["Faturamento"])
        col_sub_uni = find_col(df_sub, ["Unidades"])

        count_sub = 0
        if col_sub_cat and col_sub_name:
            for _, row in df_sub.iterrows():
                if pd.notna(row[col_sub_cat]) and pd.notna(row[col_sub_name]):
                    temp_analyzer.add_mercado_subcategoria(
                        str(row[col_sub_cat]), str(row[col_sub_name]), 
                        safe_float(row[col_sub_fat]) if col_sub_fat and col_sub_fat in row and pd.notna(row[col_sub_fat]) else 0, 
                        int(safe_float(row[col_sub_uni])) if col_sub_uni and col_sub_uni in row and pd.notna(row[col_sub_uni]) else 0
                    )
                    count_sub += 1
        
        st.session_state.analyzer = temp_analyzer
        st.session_state['data_version'] = datetime.now().timestamp()
        
        detalhes = []
        if fat_3m > 0: detalhes.append(f"Faturamento: {format_br(fat_3m)}")
        if ticket_medio > 0: detalhes.append(f"Ticket: {format_br(ticket_medio)}")
        
        info_msg = f"✅ **{empresa}** importada com sucesso!\n\n"
        info_msg += f"- 👤 Dados Cliente: {', '.join(detalhes) if detalhes else 'OK'}\n"
        info_msg += f"- 📈 Categorias Macro: {count_cat} registros\n"
        info_msg += f"- 🎯 Subcategorias: {count_sub} registros"
        
        st.session_state['last_upload_info'] = info_msg
        return True
    except Exception as e:
        st.error(f"❌ Erro no processamento: {str(e)}")
        st.info("Dica: Verifique se as abas 'Cliente', 'Mercado_Categoria' e 'Mercado_Subcategoria' existem e seguem o modelo.")
        return False

# --- CSS CUSTOMIZADO DARK THEME ---
st.markdown("""
<style>
    /* Reset e Base */
    .stApp {
        background-color: #000000 !important;
    }
    
    /* Azul Noite */
    :root {
        --accent-blue: #1E3A8A;
        --accent-blue-hover: #1e40af;
    }
    
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 100%;
    }
    
    /* Sidebar Customizada */
    [data-testid="stSidebar"] {
        background-color: #0a0a0a !important;
        border-right: 1px solid #1a1a1a;
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: #FFFFFF;
    }
    
    /* Header Principal */
    .main-header {
        background: #0a0a0a;
        border: 1px solid #1a1a1a;
        border-radius: 20px;
        padding: 2.5rem;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.7);
    }
    
    .main-header h1 {
        color: #FFFFFF;
        font-size: 2.5rem;
        font-weight: bold;
        text-transform: uppercase;
        margin: 0;
        letter-spacing: 2px;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
    }
    
    .main-header p {
        color: #A0A0A0;
        font-size: 1.1rem;
        margin: 0.5rem 0 0 0;
    }
    
    /* Cards de Métricas */
    .metric-card {
        background: linear-gradient(135deg, #1a1a1a 0%, #262626 100%);
        border: 1px solid #333333;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        transition: transform 0.2s;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(30, 58, 138, 0.2);
    }
    
    .metric-label {
        font-size: 0.75rem;
        color: #A0A0A0;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.5rem;
        font-weight: 600;
    }
    
    .metric-value {
        font-size: 1.8rem;
        font-weight: bold;
        color: #FFFFFF;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
    }
    
    /* Tabs Customizadas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
        border-bottom: 2px solid #1a1a1a;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border: none;
        color: #A0A0A0;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        padding: 12px 24px;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: transparent;
        color: #1E3A8A;
        border-bottom: 3px solid #1E3A8A;
    }
    
    /* Insight Cards */
    .insight-card {
        background: linear-gradient(135deg, #1a1a1a 0%, #1e1e1e 100%);
        border: 1px solid #333333;
        border-left: 4px solid #1E3A8A;
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);
    }
    
    .insight-title {
        font-size: 1.1rem;
        font-weight: bold;
        color: #FFFFFF;
        margin-bottom: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Formulários e Inputs */
    .stTextInput input, .stNumberInput input, .stSelectbox select {
        background-color: #1a1a1a !important;
        border: 1px solid #333333 !important;
        color: #FFFFFF !important;
        border-radius: 8px;
    }
    
    .stTextInput input:focus, .stNumberInput input:focus, .stSelectbox select:focus {
        border-color: #1E3A8A !important;
        box-shadow: 0 0 0 1px #1E3A8A !important;
    }
    
    /* Botões */
    .stButton button {
        background: linear-gradient(135deg, #1E3A8A 0%, #1e40af 100%);
        color: #FFFFFF;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.5rem;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.3s;
    }
    
    .stButton button:hover {
        background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
        box-shadow: 0 4px 12px rgba(30, 58, 138, 0.4);
        transform: translateY(-2px);
    }
    
    /* Dataframes */
    .stDataFrame {
        background-color: #1a1a1a;
        border: 1px solid #333333;
        border-radius: 8px;
    }
    
    /* Expanders */
    .streamlit-expanderHeader {
        background-color: #1a1a1a !important;
        border: 1px solid #333333 !important;
        border-radius: 8px !important;
        color: #FFFFFF !important;
    }
    
    /* File Uploader */
    [data-testid="stFileUploader"] {
        background-color: #1a1a1a;
        border: 2px dashed #333333;
        border-radius: 8px;
        padding: 1rem;
    }
    
    /* Texto Geral */
    p, span, div, label {
        color: #E0E0E0 !important;
    }
    
    h1, h2, h3, h4, h5, h6 {
        color: #FFFFFF !important;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: #0a0a0a;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #333333;
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #1E3A8A;
    }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    # Logo e Título
    st.markdown(f"""
    <div style="text-align: center; padding: 1rem 0 2rem 0;">
        <div style="width: 60px; height: 60px; background: #1a1a1a; border: 1px solid #333; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 1.5rem auto;">
            {SVG_ICONS["chart"]}
        </div>
        <div style="font-size: 1.2rem; font-weight: bold; color: #FFFFFF; text-transform: uppercase; letter-spacing: 3px;">
            Inteligência de Mercado
        </div>
        <div style="font-size: 0.8rem; color: #A0A0A0; margin-top: 0.5rem; line-height: 1.4;">
            Inteligência de dados aplicada à expansão do seu negócio.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Upload de Dados
    st.markdown(f"""
    <div style="margin-bottom: 1.5rem;">
        <div style="display: flex; align-items: center; margin-bottom: 0.8rem;">
            <div style="width: 32px; height: 32px; background: #1a1a1a; border: 1px solid #333; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 12px;">
                {SVG_ICONS["box"]}
            </div>
            <span style="font-size: 1rem; font-weight: bold; color: #FFFFFF; text-transform: uppercase; letter-spacing: 1px;">Upload de Dados</span>
        </div>
        <div style="font-size: 0.8rem; color: #A0A0A0; margin-left: 44px;">Mercado Livre ou Shopee</div>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("Arraste ou selecione sua planilha", type=["xlsx"], key="excel_uploader_v5", label_visibility="collapsed")
    if uploaded_file is not None:
        if st.button("🚀 Processar Planilha", use_container_width=True):
            if processar_excel(uploaded_file):
                st.success("Dados carregados!")
                st.rerun()
    
    if 'last_upload_info' in st.session_state:
        st.info(st.session_state.last_upload_info)
    
    st.markdown("---")
    
    # Gerar Relatório
    st.markdown(f"""
    <div style="margin-bottom: 1.5rem;">
        <div style="display: flex; align-items: center; margin-bottom: 0.8rem;">
            <div style="width: 32px; height: 32px; background: #1a1a1a; border: 1px solid #333; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 12px;">
                {SVG_ICONS["file"]}
            </div>
            <span style="font-size: 1rem; font-weight: bold; color: #FFFFFF; text-transform: uppercase; letter-spacing: 1px;">Relatório Executivo</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    current_analyzer = st.session_state.analyzer

    if st.button("Gerar Relatório PDF", use_container_width=True, key="pdf_button"):
        if current_analyzer.cliente_data:
            # Tentar obter o ranking para o PDF
            df_rank_pdf = current_analyzer.gerar_ranking()
            if not df_rank_pdf.empty:
                with st.spinner("Gerando relatório..."):
                    try:
                        # Coletar dados de foco para o PDF
                        cat_foco = st.session_state.get("selected_macro_cat")
                        sub_foco = st.session_state.get("selected_sub_cat_foco")
                        
                        # Se não houver seleção no session_state, pega o primeiro do ranking
                        if not sub_foco:
                            sub_foco = df_rank_pdf.iloc[0]["Subcategoria"]
                            cat_foco = df_rank_pdf.iloc[0]["Categoria Macro"]
                            
                        row_foco_pdf = df_rank_pdf[df_rank_pdf["Subcategoria"] == sub_foco].iloc[0]
                        
                        # Gerar imagens dos gráficos para o PDF
                        chart_images = {}
                        try:
                            import io
                            from PIL import Image
                            
                            # 1. Gauge Score
                            fig_gauge = criar_gauge_score(row_foco_pdf['Score'], row_foco_pdf['Status'])
                            # Tentativa 1: Kaleido
                            try:
                                chart_images['score_gauge'] = fig_gauge.to_image(format="png", engine="kaleido", width=600, height=400, scale=2)
                            except:
                                # Fallback: Se kaleido falhar, não geramos erro, o PDF tratará a ausência
                                pass
                            
                            # 2. Comparação de Tickets
                            r_perm = current_analyzer.cliente_data.get('range_permitido', 0.20)
                            res_sim = current_analyzer.simular_cenarios(cat_foco, sub_foco)
                            l_inf, l_sup = calcular_limites_ticket_local(res_sim['ticket_mercado'], r_perm)
                            fig_ticket = criar_comparacao_tickets(res_sim['ticket_mercado'], row_foco_pdf['Ticket Cliente'], l_inf, l_sup)
                            try:
                                chart_images['ticket_comp'] = fig_ticket.to_image(format="png", engine="kaleido", width=600, height=400, scale=2)
                            except:
                                pass
                        except Exception as img_err:
                            st.warning(f"Aviso: Os gráficos serão exibidos apenas como texto no PDF devido a uma limitação técnica temporária.")
                            chart_images = {}

                        pdf_gen = PDFReportGenerator(
                            analyzer=current_analyzer,
                            cliente_data=current_analyzer.cliente_data,
                            cat_foco=cat_foco,
                            sub_foco=sub_foco,
                            row_foco=row_foco_pdf,
                            chart_images=chart_images
                        )
                        pdf_buffer = pdf_gen.gerar_relatorio()
                        st.download_button(
                            label="📥 Download PDF",
                            data=pdf_buffer,
                            file_name=f"relatorio_mercado_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                        st.success("✅ Relatório gerado com sucesso!")
                    except Exception as e:
                        st.error(f"Erro ao gerar PDF: {str(e)}")
            else:
                st.warning("É necessário ter subcategorias cadastradas para gerar o relatório.")
        else:
            st.warning("Adicione dados do cliente antes de gerar o relatório.")

# --- CONTEÚDO PRINCIPAL ---

analyzer = st.session_state.analyzer

# Header Principal
st.markdown(f"""
<div class="main-header">
    <div style="display: flex; align-items: center;">
        <div style="width: 80px; height: 80px; background: #1a1a1a; border: 1px solid #333; border-radius: 20px; display: flex; align-items: center; justify-content: center; margin-right: 1.5rem;">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>
        </div>
        <div>
            <h1 style="margin: 0; font-size: 2.2rem; letter-spacing: 3px; font-weight: 800;">INTELIGÊNCIA DE MERCADO</h1>
            <p style="margin: 0.5rem 0 0 0; font-size: 1rem; color: #A0A0A0; opacity: 0.8;">Inteligência de dados aplicada à expansão do seu negócio.</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Navegação por Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "DASHBOARD",
    "DADOS DO CLIENTE",
    "GESTÃO DE CATEGORIAS",
    "MERCADO SUBCATEGORIAS",
    "ANÁLISE EXECUTIVA"
])

# ====================
# TAB 1: DASHBOARD (INÍCIO)
# ====================
with tab1:
    st.markdown(f"""
    <div style="display: flex; align-items: center; margin-bottom: 1.5rem;">
        <div style="width: 32px; height: 32px; background: #1a1a1a; border: 1px solid #333; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 12px;">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg>
        </div>
        <h2 style="margin: 0;">Visão Geral do Sistema</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Métricas Principais
    total_categorias = len(analyzer.mercado_categoria)
    total_subcategorias = sum(len(subs) for subs in analyzer.mercado_subcategorias.values())
    
    # Calcular totais
    faturamento_total = 0
    unidades_total = 0
    
    for cat_data in analyzer.mercado_categoria.values():
        for periodo in cat_data:
            faturamento_total += periodo.get('faturamento', 0)
            unidades_total += periodo.get('unidades', 0)
    
    ticket_medio = faturamento_total / unidades_total if unidades_total > 0 else 0
    
    # Grid de Cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(criar_metric_card(SVG_ICONS["box"], "CATEGORIAS MACRO", str(total_categorias)), unsafe_allow_html=True)
    
    with col2:
        st.markdown(criar_metric_card(SVG_ICONS["dollar"], "FATURAMENTO TOTAL", f"R$ {format_br(faturamento_total)}"), unsafe_allow_html=True)
    
    with col3:
        st.markdown(criar_metric_card(SVG_ICONS["chart"], "SUBCATEGORIAS", str(total_subcategorias)), unsafe_allow_html=True)
    
    with col4:
        st.markdown(criar_metric_card(SVG_ICONS["target"], "TICKET MÉDIO", f"R$ {format_br(ticket_medio)}"), unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Informações do Cliente
    if analyzer.cliente_data:
        st.markdown(f"""
        <div style="display: flex; align-items: center; margin: 2rem 0 1.5rem 0;">
            <div style="width: 32px; height: 32px; background: #1a1a1a; border: 1px solid #333; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 12px;">
                {SVG_ICONS["user"]}
            </div>
            <h3 style="margin: 0;">Informações do Cliente</h3>
        </div>
        """, unsafe_allow_html=True)
        
        col_info1, col_info2, col_info3 = st.columns(3)
        
        with col_info1:
            st.markdown(f"""
            <div class="insight-card">
                <div class="insight-title">Empresa</div>
                <div style="font-size: 1.3rem; color: #3b82f6;">{analyzer.cliente_data.get('empresa', 'N/A')}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_info2:
            st.markdown(f"""
            <div class="insight-card">
                <div class="insight-title">Categoria</div>
                <div style="font-size: 1.3rem; color: #3b82f6;">{analyzer.cliente_data.get('categoria_principal', analyzer.cliente_data.get('categoria', 'N/A'))}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_info3:
            st.markdown(f"""
            <div class="insight-card">
                <div class="insight-title">Ticket Médio</div>
                <div style="font-size: 1.3rem; color: #3b82f6;">R$ {format_br(analyzer.cliente_data.get('ticket_medio', 0))}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("📋 Configure os dados do cliente na aba 'DADOS DO CLIENTE' para começar a análise.")
    
    # Guia Rápido
    st.markdown("---")
    st.markdown("### 📖 Guia Rápido")
    
    with st.expander("Como usar este sistema"):
        st.markdown("""
        **Passo 1: Dados do Cliente**
        Configure as informações básicas da sua empresa, incluindo ticket médio, margem e faturamento.
        
        **Passo 2: Gestão de Categorias**
        Adicione dados históricos das categorias macro que você deseja analisar.
        
        **Passo 3: Mercado Subcategorias**
        Cadastre as subcategorias específicas com dados de faturamento e unidades vendidas.
        
        **Passo 4: Análise Executiva**
        Visualize o ranking automático, simulações de cenários e recomendações estratégicas.
        
        **Atalho: Importar Excel**
        Use a sidebar para importar uma planilha Excel com todos os dados de uma vez.
        """)

# ====================
# TAB 2: DADOS DO CLIENTE
# ====================
with tab2:
    st.markdown("## 👤 Configuração dos Dados do Cliente")
    
    with st.form("form_cliente"):
        st.markdown("### Informações Básicas")
        col1, col2 = st.columns(2)
        empresa = col1.text_input("Nome da Empresa", value=analyzer.cliente_data.get('empresa', ''))
        categoria = col2.text_input("Categoria Macro", value=analyzer.cliente_data.get('categoria', ''))
        
        st.markdown("### Dados Financeiros")
        col3, col4 = st.columns(2)
        ticket_medio = col3.number_input("Ticket Médio (R$)", min_value=0.0, value=float(analyzer.cliente_data.get('ticket_medio', 0.0)), step=0.01)
        margem = col4.number_input("Margem de Lucro (%)", min_value=0.0, max_value=100.0, value=float(analyzer.cliente_data.get('margem', 0.0) * 100), step=0.1) / 100
        
        st.markdown("### Desempenho Recente (Últimos 3 Meses)")
        col5, col6 = st.columns(2)
        faturamento_3m = col5.number_input("Faturamento Médio (R$)", min_value=0.0, value=float(analyzer.cliente_data.get('faturamento_3m', 0.0)), step=0.01)
        unidades_3m = col6.number_input("Unidades Vendidas", min_value=0, value=int(analyzer.cliente_data.get('unidades_3m', 0)), step=1)
        
        st.markdown("### Configurações Avançadas")
        col7, col8 = st.columns(2)
        range_permitido = col7.number_input("Range de Ticket Permitido (%)", min_value=0.0, max_value=100.0, value=float(analyzer.cliente_data.get('range_permitido', 0.20) * 100), step=1.0) / 100
        ticket_custom = col8.number_input("Ticket Customizado (Opcional)", min_value=0.0, value=float(analyzer.cliente_data.get('ticket_custom', 0.0) if analyzer.cliente_data.get('ticket_custom') else 0.0), step=0.01)
        
        if st.form_submit_button("💾 Salvar Dados do Cliente", use_container_width=True):
            analyzer.set_cliente_data(
                empresa=empresa,
                categoria=categoria,
                ticket_medio=ticket_medio,
                margem=margem,
                faturamento_3m=faturamento_3m,
                unidades_3m=unidades_3m,
                range_permitido=range_permitido,
                ticket_custom=ticket_custom if ticket_custom > 0 else None
            )
            st.success("✅ Dados salvos com sucesso!")
            st.rerun()
    
    # Resumo dos Dados
    if analyzer.cliente_data:
        st.markdown("---")
        st.markdown("### 📊 Resumo dos Dados Configurados")
        
        dados_resumo = {
            "Campo": ["Empresa", "Categoria", "Ticket Médio", "Margem", "Faturamento 3M", "Unidades 3M"],
            "Valor": [
                analyzer.cliente_data.get('empresa', 'N/A'),
                analyzer.cliente_data.get('categoria', 'N/A'),
                f"R$ {format_br(analyzer.cliente_data.get('ticket_medio', 0))}",
                f"{analyzer.cliente_data.get('margem', 0) * 100:.1f}%",
                f"R$ {format_br(analyzer.cliente_data.get('faturamento_3m', 0))}",
                str(analyzer.cliente_data.get('unidades_3m', 0))
            ]
        }
        
        df_resumo = pd.DataFrame(dados_resumo)
        st.dataframe(df_resumo, use_container_width=True, hide_index=True)

# ====================
# TAB 3: GESTÃO DE CATEGORIAS
# ====================
with tab3:
    st.markdown("## 📈 Gestão de Categorias Macro")
    
    with st.form("nova_categoria"):
        st.markdown("### Adicionar Nova Categoria")
        col1, col2 = st.columns(2)
        cat_nome = col1.text_input("Nome da Categoria")
        periodo = col2.text_input("Período (ex: 2024-01)")
        
        col3, col4 = st.columns(2)
        faturamento = col3.text_input("Faturamento (R$)")
        unidades = col4.text_input("Unidades Vendidas")
        
        if st.form_submit_button("➕ Adicionar Categoria", use_container_width=True):
            if cat_nome and periodo:
                analyzer.add_mercado_categoria(cat_nome, periodo, parse_large_number(faturamento), int(parse_large_number(unidades)))
                st.success(f"✅ Categoria '{cat_nome}' adicionada!")
                st.rerun()
            else:
                st.warning("Preencha pelo menos o nome e o período.")
    
    st.markdown("---")
    st.markdown("### 📋 Categorias Cadastradas")
    
    if analyzer.mercado_categoria:
        for cat, periodos in analyzer.mercado_categoria.items():
            with st.expander(f"📁 {cat} ({len(periodos)} períodos)"):
                df_cat = pd.DataFrame(periodos)
                
                if not df_cat.empty:
                    df_cat['ticket_medio'] = df_cat.apply(
                        lambda row: row['faturamento'] / row['unidades'] if row['unidades'] > 0 else 0,
                        axis=1
                    )
                    
                    # Editar períodos
                    st.markdown("#### ✏️ Editar Períodos")
                    for i, row in df_cat.iterrows():
                        with st.form(f"edit_cat_{cat}_{i}"):
                            c1, c2, c3, c4 = st.columns(4)
                            new_per = c1.text_input("Período", value=row['periodo'])
                            new_fat = c2.text_input("Faturamento", value=str(row['faturamento']))
                            new_uni = c3.text_input("Unidades", value=str(row['unidades']))
                            
                            b1, b2 = st.columns(2)
                            if b1.form_submit_button("💾 Salvar"):
                                analyzer.editar_mercado_categoria(cat, row['periodo'], new_per, parse_large_number(new_fat), int(parse_large_number(new_uni)))
                                st.rerun()
                            if b2.form_submit_button("🗑️ Excluir"):
                                analyzer.remover_periodo_categoria(cat, row['periodo'])
                                st.rerun()
                    
                    # Tabela de Dados
                    st.markdown("#### 📊 Dados da Categoria")
                    df_disp = df_cat.copy()
                    df_disp['faturamento'] = df_disp['faturamento'].apply(format_br)
                    df_disp['ticket_medio'] = df_disp['ticket_medio'].apply(format_br)
                    st.dataframe(df_disp, use_container_width=True)
                    
                    # Visualizações
                    st.markdown("#### 📈 Visualizações")
                    tab_viz1, tab_viz2 = st.tabs(["Evolução da Categoria", "Ticket Médio"])
                    with tab_viz1:
                        st.plotly_chart(criar_grafico_evolucao_categoria(df_cat), use_container_width=True)
                    with tab_viz2:
                        st.plotly_chart(criar_grafico_ticket_medio(df_cat), use_container_width=True)
    else:
        st.info("Nenhuma categoria macro cadastrada.")

# ====================
# TAB 4: SUBCATEGORIAS
# ====================
with tab4:
    st.markdown("## 🎯 Mercado de Subcategorias")
    
    categorias = list(analyzer.mercado_categoria.keys())
    if not categorias:
        st.warning("⚠️ Cadastre uma Categoria Macro primeiro na aba 'GESTÃO DE CATEGORIAS'!")
    else:
        cat_sel = st.selectbox("Selecione a Categoria Macro:", categorias)
        
        with st.form("nova_sub"):
            st.markdown("### Adicionar Nova Subcategoria")
            sub = st.text_input("Nome da Subcategoria")
            col1, col2 = st.columns(2)
            fat_6m = col1.text_input("Faturamento 6M (R$)")
            uni_6m = col2.text_input("Unidades 6M")
            
            if st.form_submit_button("➕ Adicionar Subcategoria", use_container_width=True):
                if sub:
                    analyzer.add_mercado_subcategoria(cat_sel, sub, parse_large_number(fat_6m), int(parse_large_number(uni_6m)))
                    st.success(f"✅ Subcategoria '{sub}' adicionada!")
                    st.rerun()
        
        st.markdown("---")
        
        if cat_sel in analyzer.mercado_subcategorias:
            subcategorias_lista = analyzer.mercado_subcategorias[cat_sel]
            
            st.markdown("### 📋 Lista de Subcategorias")
            if not subcategorias_lista:
                st.info("Nenhuma subcategoria cadastrada para esta categoria macro.")
            else:
                df_sub_raw = pd.DataFrame(subcategorias_lista)
                
                # Tabela de visualização
                df_sub_disp = df_sub_raw.copy()
                df_sub_disp['faturamento_6m'] = df_sub_disp['faturamento_6m'].apply(format_br)
                df_sub_disp['ticket_medio'] = df_sub_disp['ticket_medio'].apply(format_br)
                st.dataframe(df_sub_disp, use_container_width=True)
                
                st.markdown("#### ✏️ Editar Subcategorias")
                for i, row in df_sub_raw.iterrows():
                    with st.expander(f"Editar: {row['subcategoria']}"):
                        with st.form(f"edit_sub_{cat_sel}_{i}"):
                            c1, c2, c3 = st.columns(3)
                            new_sub = c1.text_input("Nome Subcategoria", value=row['subcategoria'])
                            new_fat = c2.text_input("Faturamento 6M (R$)", value=str(row['faturamento_6m']))
                            new_uni = c3.text_input("Unidades 6M", value=str(row['unidades_6m']))
                            
                            b1, b2 = st.columns(2)
                            if b1.form_submit_button("💾 Salvar Alterações"):
                                analyzer.editar_mercado_subcategoria(cat_sel, row['subcategoria'], new_sub, parse_large_number(new_fat), int(parse_large_number(new_uni)))
                                st.rerun()
                            if b2.form_submit_button("🗑️ Excluir Subcategoria", type="secondary"):
                                analyzer.remover_mercado_subcategoria(cat_sel, row['subcategoria'])
                                st.rerun()

# ====================
# TAB 5: ANÁLISE EXECUTIVA (DASHBOARD)
# ====================
with tab5:
    st.markdown("## 📊 Análise Executiva e Simulações")
    
    df_ranking = analyzer.gerar_ranking()
    if df_ranking.empty:
        st.info("📋 Importe ou adicione dados nas abas anteriores para visualizar a análise executiva.")
    else:
        # Ranking de Oportunidades
        col_rank1, col_rank2 = st.columns([1, 1])
        with col_rank1:
            st.markdown("### 🏆 Ranking de Oportunidades")
            df_display = df_ranking[['Categoria Macro', 'Subcategoria', 'Score', 'Status']].copy()
            st.dataframe(df_display, use_container_width=True)
        with col_rank2:
            st.plotly_chart(criar_grafico_ranking_subcategorias(df_ranking), use_container_width=True)
        
        st.markdown("---")
        
        # Análise Detalhada
        sub_foco_dashboard = st.selectbox("Selecione uma Subcategoria para Análise Detalhada:", df_ranking["Subcategoria"].tolist(), key="dashboard_sub_foco_selector")
        st.session_state["selected_sub_cat_foco"] = sub_foco_dashboard
        
        row_foco = df_ranking[df_ranking["Subcategoria"] == sub_foco_dashboard].iloc[0]
        st.session_state["selected_macro_cat"] = row_foco["Categoria Macro"]
        
        # Simulação de Cenários
        st.markdown("### 💰 Simulação de Cenários")
        
        with st.expander("⚙️ Ajustar Metas de Share", expanded=False):
            col_s1, col_s2, col_s3 = st.columns(3)
            s_cons = col_s1.slider("Share Conservador (%)", 0.0, 5.0, 0.2, 0.1) / 100
            s_prov = col_s2.slider("Share Provável (%)", 0.0, 10.0, 0.5, 0.1) / 100
            s_otim = col_s3.slider("Share Otimista (%)", 0.0, 20.0, 1.0, 0.1) / 100
        
        custom_shares = {
            'Conservador': {'share_alvo': s_cons, 'label': f"{s_cons*100:.1f}%"},
            'Provável': {'share_alvo': s_prov, 'label': f"{s_prov*100:.1f}%"},
            'Otimista': {'share_alvo': s_otim, 'label': f"{s_otim*100:.1f}%"}
        }
        
        res = analyzer.simular_cenarios(row_foco['Categoria Macro'], sub_foco_dashboard, custom_shares)
        
        # Cards de Indicadores
        st.markdown("#### 📈 Indicadores de Market Share")
        m1, m2, m3, m4, m5 = st.columns(5)
        
        share_atual_calc = analyzer.calcular_share_atual(res['mercado_6m'])
        
        with m1:
            st.markdown(criar_metric_card("💼", "Tamanho Mercado (6M)", f"R$ {format_br(res['mercado_6m'])}"), unsafe_allow_html=True)
        with m2:
            st.markdown(criar_metric_card("📊", "Seu Share Atual", f"{share_atual_calc:.2f}%"), unsafe_allow_html=True)
        with m3:
            share_alvo = custom_shares['Provável']['share_alvo'] * 100
            st.markdown(criar_metric_card("🎯", "Meta de Share", f"{share_alvo:.1f}%"), unsafe_allow_html=True)
        with m4:
            st.markdown(criar_metric_card("💰", "Ticket Mercado", f"R$ {format_br(res['ticket_mercado'])}"), unsafe_allow_html=True)
        with m5:
            st.markdown(criar_metric_card("📈", "Sua Margem", f"{analyzer.cliente_data.get('margem', 0)*100:.1f}%"), unsafe_allow_html=True)
        
        # Gráficos de Score e Ticket
        g1, g2 = st.columns(2)
        with g1:
            st.plotly_chart(criar_gauge_score(row_foco['Score'], row_foco['Status']), use_container_width=True)
        with g2:
            r_perm = analyzer.cliente_data.get('range_permitido', 0.20)
            l_inf, l_sup = calcular_limites_ticket_local(res['ticket_mercado'], r_perm)
            st.plotly_chart(criar_comparacao_tickets(res['ticket_mercado'], row_foco['Ticket Cliente'], l_inf, l_sup), use_container_width=True)
        
        # Projeções de Receita e Lucro
        st.markdown("#### 📈 Projeções de Receita e Lucro")
        df_cen = res['cenarios'].copy()
        
        c_tab1, c_tab2 = st.tabs(["Tabela de Dados", "Gráfico Comparativo"])
        with c_tab1:
            df_disp_cen = df_cen.copy()
            df_disp_cen['Receita Projetada 6M'] = df_disp_cen['Receita Projetada 6M'].apply(format_br)
            df_disp_cen['Lucro Projetado 6M'] = df_disp_cen['Lucro Projetado 6M'].apply(format_br)
            df_disp_cen['Delta vs Atual'] = df_disp_cen['Delta vs Atual'].apply(format_br)
            df_disp_cen['Crescimento (%)'] = df_disp_cen['Crescimento (%)'].apply(lambda x: f"{x:,.1f}%".replace(",", "X").replace(".", ",").replace("X", "."))
            st.dataframe(df_disp_cen, use_container_width=True)
        with c_tab2:
            st.plotly_chart(criar_grafico_cenarios(df_cen), use_container_width=True)
        
        # Tendência e Projeção
        st.markdown("---")
        st.markdown("### 📈 Tendência e Projeção de Demanda")
        
        confianca = analyzer.calcular_confianca(row_foco['Categoria Macro'], sub_foco_dashboard)
        cor_conf = "green" if confianca['nivel'] == "Alta" else ("orange" if confianca['nivel'] == "Média" else "red")
        
        st.markdown(f"**Índice de Confiança da Projeção:** <span style='color:{cor_conf}; font-weight:bold;'>{confianca['score']}% ({confianca['nivel']})</span>", unsafe_allow_html=True)
        
        if confianca['motivos']:
            with st.expander("Ver detalhes da confiabilidade"):
                for m in confianca['motivos']:
                    st.write(f"• {m}")
        
        tendencia_res = analyzer.calcular_tendencia(row_foco['Categoria Macro'])
        
        t_col1, t_col2, t_col3 = st.columns([1, 1, 2])
        with t_col1:
            st.metric("Tendência Atual", tendencia_res['tendencia'], delta=f"{tendencia_res['crescimento_mensal']:.1f}% mensal")
        with t_col2:
            st.metric("Projeção Total (3 Meses)", f"R$ {format_br(tendencia_res['projecao_3m'])}")
        with t_col3:
            meses = ["Mês 1", "Mês 2", "Mês 3"]
            valores = tendencia_res.get('mensal', [0, 0, 0])
            df_proj = pd.DataFrame({"Mês": meses, "Faturamento": valores})
            
            # Calcular um range seguro para o eixo Y não cortar o texto
            max_val = max(valores) if valores else 0
            y_range = [0, max_val * 1.25] if max_val > 0 else [0, 100]

            fig_proj = px.bar(df_proj, x="Mês", y="Faturamento",
                             text=[f"R$ {format_br(v)}" for v in valores],
                             title="Projeção Mensal Detalhada",
                             color_discrete_sequence=["#1E3A8A"])
            
            fig_proj.update_traces(
                textposition='outside',
                textfont=dict(size=11, color='#FFFFFF'),
                cliponaxis=False  # Garante que o texto não seja cortado pelas bordas
            )
            
            fig_proj.update_layout(
                height=300, # Aumentado levemente para melhor respiro
                margin=dict(l=10, r=10, t=50, b=10), # Mais margem no topo para o título e valores
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#FFFFFF'),
                yaxis=dict(
                    range=y_range,
                    showgrid=True,
                    gridcolor='rgba(255,255,255,0.1)',
                    zeroline=True,
                    zerolinecolor='rgba(255,255,255,0.2)'
                ),
                xaxis=dict(showgrid=False)
            )
            st.plotly_chart(fig_proj, use_container_width=True)
        
        # Plano de Ação
        st.markdown("---")
        st.markdown("### 🧠 Plano de Ação Sugerido")
        plano = analyzer.gerar_plano_acao(row_foco['Categoria Macro'])
        sub_plano = next((p for p in plano if p['Subcategoria'] == sub_foco_dashboard), None)
        
        if sub_plano:
            lista_acoes = sub_plano.get('Ações', [])
            if not lista_acoes and 'Recomendação' in sub_plano:
                lista_acoes = [sub_plano['Recomendação']]
            
            acoes_html = "".join([f"<li style='margin-bottom: 8px;'>{acao}</li>" for acao in lista_acoes])
            
            st.markdown(f"""
            <div class="insight-card" style="border-left-color: {sub_plano.get('Cor', '#1E3A8A')};">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                    <span style="font-size: 1.3rem; font-weight: bold; color: {sub_plano.get('Cor', '#1E3A8A')};">🎯 Prioridade: {sub_plano.get('Prioridade', 'N/A')}</span>
                    <span style="background-color: {sub_plano.get('Cor', '#1E3A8A')}; color: #FFFFFF; padding: 4px 12px; border-radius: 15px; font-size: 0.9rem; font-weight: bold;">Score: {sub_plano.get('Score', 0):.2f}</span>
                </div>
                <ul style="list-style-type: none; padding-left: 0; font-size: 1.1rem; color: #E0E0E0;">
                    {acoes_html}
                </ul>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("Não foi possível gerar recomendações para esta subcategoria.")
        
        # Insights dos Cenários
        st.markdown("### 💡 Insights dos Cenários")
        
        fat_base_3m = float(analyzer.cliente_data.get('faturamento_3m', 0))
        if fat_base_3m == 0:
            st.warning("⚠️ Seu faturamento atual está zerado nos 'Dados do Cliente'. As porcentagens de crescimento podem não refletir a realidade.")
        
        i_col1, i_col2, i_col3 = st.columns(3)
        
        with i_col1:
            row = df_cen.iloc[0]
            c_val = row['Crescimento (%)']
            c_color = "#2ecc71" if c_val > 0 else ("#e74c3c" if c_val < 0 else "#A0A0A0")
            st.markdown(f"""
            <div class="insight-card" style="border-left-color: #2ecc71;">
                <div class="insight-title">🟢 Cenário Conservador</div>
                • Receita: R$ {format_br(row['Receita Projetada 6M'])}<br>
                • Lucro: R$ {format_br(row['Lucro Projetado 6M'])}<br>
                • Crescimento: <span style="color: {c_color}; font-weight: bold;">{c_val:,.1f}%</span>
            </div>
            """, unsafe_allow_html=True)
        
        with i_col2:
            row = df_cen.iloc[1]
            c_val = row['Crescimento (%)']
            c_color = "#2ecc71" if c_val > 0 else ("#e74c3c" if c_val < 0 else "#A0A0A0")
            st.markdown(f"""
            <div class="insight-card" style="border-left-color: #f1c40f;">
                <div class="insight-title">🟡 Cenário Provável</div>
                • Receita: R$ {format_br(row['Receita Projetada 6M'])}<br>
                • Lucro: R$ {format_br(row['Lucro Projetado 6M'])}<br>
                • Crescimento: <span style="color: {c_color}; font-weight: bold;">{c_val:,.1f}%</span>
            </div>
            """, unsafe_allow_html=True)
        
        with i_col3:
            row = df_cen.iloc[2]
            c_val = row['Crescimento (%)']
            c_color = "#2ecc71" if c_val > 0 else ("#e74c3c" if c_val < 0 else "#A0A0A0")
            st.markdown(f"""
            <div class="insight-card" style="border-left-color: #e74c3c;">
                <div class="insight-title">🔴 Cenário Otimista</div>
                • Receita: R$ {format_br(row['Receita Projetada 6M'])}<br>
                • Lucro: R$ {format_br(row['Lucro Projetado 6M'])}<br>
                • Crescimento: <span style="color: {c_color}; font-weight: bold;">{c_val:,.1f}%</span>
            </div>
            """, unsafe_allow_html=True)

        # ==========================================
        # NOVO: DASHBOARD DE ANOMALIAS E OPORTUNIDADES
        # ==========================================
        st.markdown("---")
        st.markdown("### 🚨 Dashboard de Anomalias e Oportunidades")
        
        anomalias = analyzer.identificar_anomalias(row_foco['Categoria Macro'])
        
        if anomalias:
            anom_col1, anom_col2 = st.columns([2, 1])
            with anom_col1:
                for anom in anomalias:
                    cor_sev = "#FF4B4B" if anom['severidade'] == "Alta" else ("#FFA421" if anom['severidade'] == "Média" else "#1E3A8A")
                    st.markdown(f"""
                    <div class="insight-card" style="border-left-color: {cor_sev};">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                            <span style="font-weight: bold; color: #FFFFFF; font-size: 1.1rem;">{anom['tipo']}</span>
                            <span style="background-color: {cor_sev}; color: #FFFFFF; padding: 3px 10px; border-radius: 12px; font-size: 0.8rem; font-weight: bold;">{anom['severidade']}</span>
                        </div>
                        <div style="color: #E0E0E0; font-size: 1rem;">
                            <strong>{anom['subcategoria']}</strong><br>
                            {anom['mensagem']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            with anom_col2:
                st.metric("Total de Anomalias", len(anomalias), delta="Críticas detectadas")
        else:
            st.success("✅ Nenhuma anomalia crítica detectada. Seu portfólio está bem equilibrado!")
        
        # ==========================================
        # NOVO: MATRIZ DE RECOMENDAÇÃO AUTOMÁTICA (AÇÃO IMEDIATA)
        # ==========================================
        st.markdown("---")
        st.markdown("### 🎯 Matriz de Recomendação Automática (Ação Imediata)")
        
        plano_completo = analyzer.gerar_plano_acao(row_foco['Categoria Macro'])
        
        if plano_completo:
            # Criar uma tabela visual das recomendações
            rec_data = []
            for rec in plano_completo:
                rec_data.append({
                    "Subcategoria": rec['Subcategoria'],
                    "Prioridade": rec['Prioridade'],
                    "Recomendação": rec['Recomendacao_Curta'],
                    "Ação Imediata": rec['Acao_Imediata']
                })
            
            df_rec = pd.DataFrame(rec_data)
            
            # Exibir em colunas para melhor visualização
            for idx, rec in enumerate(plano_completo):
                if idx % 2 == 0:
                    rec_col1, rec_col2 = st.columns(2)
                
                col_target = rec_col1 if idx % 2 == 0 else rec_col2
                
                with col_target:
                    st.markdown(f"""
                    <div class="insight-card" style="border-left-color: {rec['Cor']}; background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                            <span style="font-weight: bold; color: #FFFFFF; font-size: 1.1rem;">{rec['Subcategoria']}</span>
                            <span style="background-color: {rec['Cor']}; color: #FFFFFF; padding: 4px 12px; border-radius: 15px; font-size: 0.8rem; font-weight: bold;">{rec['Prioridade']}</span>
                        </div>
                        <div style="margin-bottom: 10px; padding: 10px; background: rgba(255,255,255,0.05); border-radius: 8px;">
                            <div style="color: #A0A0A0; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;">Recomendação</div>
                            <div style="color: #FFFFFF; font-weight: bold; font-size: 1rem;">{rec['Recomendacao_Curta']}</div>
                        </div>
                        <div style="padding: 10px; background: rgba({rec['Cor'].lstrip('#')}, 0.1); border-radius: 8px; border-left: 3px solid {rec['Cor']};">
                            <div style=\"color: #A0A0A0; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;\">Ação Imediata</div>
                            <div style="color: #FFFFFF; font-size: 0.95rem;">{rec['Acao_Imediata']}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        
        # ==========================================
        # NOVO: SIMULADOR WHAT-IF (O que acontece se...?)
        # ==========================================
        st.markdown("---")
        st.markdown("### 🔮 Simulador What-if (O que acontece se...?)")
        
        with st.expander("⚙️ Simular Mudanças de Preço e Volume", expanded=False):
            sim_col1, sim_col2, sim_col3 = st.columns(3)
            
            with sim_col1:
                preco_change = st.slider("Mudança de Preço (%)", -50.0, 50.0, 0.0, 5.0, key="price_sim")
            
            with sim_col2:
                volume_change = st.slider("Mudança de Volume (%)", -50.0, 100.0, 0.0, 5.0, key="volume_sim")
            
            with sim_col3:
                st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
                simular_btn = st.button("🚀 Simular Cenário", use_container_width=True)
            
            if simular_btn or 'what_if_result' in st.session_state:
                # Calcular impacto
                ticket_atual = float(row_foco['Ticket Cliente'])
                novo_ticket = ticket_atual * (1 + preco_change / 100)
                
                fat_atual = float(analyzer.cliente_data.get('faturamento_3m', 0))
                novo_fat = fat_atual * (1 + volume_change / 100)
                
                margem = float(analyzer.cliente_data.get('margem', 0.35))
                lucro_atual = fat_atual * margem
                lucro_novo = novo_fat * margem
                delta_lucro = lucro_novo - lucro_atual
                
                # Exibir resultados
                st.markdown("#### 📊 Resultado da Simulação")
                
                sim_res_col1, sim_res_col2, sim_res_col3, sim_res_col4 = st.columns(4)
                
                with sim_res_col1:
                    st.markdown(f"""
                    <div class="insight-card">
                        <div class="insight-title">Novo Ticket</div>
                        <div style="font-size: 1.5rem; color: #1E3A8A; font-weight: bold;">R$ {format_br(novo_ticket)}</div>
                        <div style="font-size: 0.85rem; color: #A0A0A0; margin-top: 5px;">
                            Mudança: <span style="color: {'#2ecc71' if novo_ticket > ticket_atual else '#e74c3c'}; font-weight: bold;">{preco_change:+.1f}%</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with sim_res_col2:
                    st.markdown(f"""
                    <div class="insight-card">
                        <div class="insight-title">Novo Faturamento</div>
                        <div style="font-size: 1.5rem; color: #1E3A8A; font-weight: bold;">R$ {format_br(novo_fat)}</div>
                        <div style="font-size: 0.85rem; color: #A0A0A0; margin-top: 5px;">
                            Mudança: <span style="color: {'#2ecc71' if novo_fat > fat_atual else '#e74c3c'}; font-weight: bold;">{volume_change:+.1f}%</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with sim_res_col3:
                    st.markdown(f"""
                    <div class="insight-card">
                        <div class="insight-title">Novo Lucro (3M)</div>
                        <div style="font-size: 1.5rem; color: #1E3A8A; font-weight: bold;">R$ {format_br(lucro_novo)}</div>
                        <div style="font-size: 0.85rem; color: #A0A0A0; margin-top: 5px;">
                            Margem: {margem*100:.1f}%
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with sim_res_col4:
                    delta_pct = (delta_lucro / lucro_atual * 100) if lucro_atual > 0 else 0
                    cor_delta = "#2ecc71" if delta_lucro > 0 else "#e74c3c"
                    st.markdown(f"""
                    <div class="insight-card">
                        <div class="insight-title">Impacto no Lucro</div>
                        <div style="font-size: 1.5rem; color: {cor_delta}; font-weight: bold;">R$ {format_br(abs(delta_lucro))}</div>
                        <div style="font-size: 0.85rem; color: #A0A0A0; margin-top: 5px;">
                            <span style="color: {cor_delta}; font-weight: bold;">{delta_pct:+.1f}%</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Insight da simulação
                st.markdown("#### 💡 Insight da Simulação")
                if preco_change > 0 and volume_change < 0:
                    insight = f"⚠️ **Atenção**: Aumentar preço em {preco_change:.1f}% pode reduzir volume em {abs(volume_change):.1f}%. Avalie a elasticidade do seu produto."
                elif preco_change < 0 and volume_change > 0:
                    insight = f"✅ **Oportunidade**: Reduzir preço em {abs(preco_change):.1f}% pode aumentar volume em {volume_change:.1f}%. Verifique se a margem continua saudável."
                elif delta_lucro > 0:
                    insight = f"🚀 **Positivo**: Este cenário aumentaria seu lucro em R$ {format_br(delta_lucro)}. Considere implementar."
                else:
                    insight = f"📉 **Cuidado**: Este cenário reduziria seu lucro em R$ {format_br(abs(delta_lucro))}. Revise a estratégia."
                
                st.info(insight)
