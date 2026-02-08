#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aplicação Streamlit - Tamanho do Mercado
Dashboard interativo para análise estratégica de múltiplas categorias macro
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
    page_title="Tamanho do Mercado",
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

# --- INICIALIZAÇÃO ---

# Garantir que o analyzer esteja sempre na sessão e atualizado
if 'analyzer' not in st.session_state:
    st.session_state.analyzer = MarketAnalyzer()
else:
    # Verificação de segurança: se o objeto na sessão não tem os métodos novos, forçamos a atualização
    # sem perder os dados, se possível, ou reiniciamos para evitar o erro de AttributeError
    if not hasattr(st.session_state.analyzer, 'editar_mercado_categoria') or not hasattr(st.session_state.analyzer, 'remover_periodo_categoria'):
        # Tentar migrar dados para um novo objeto que possui os métodos
        old_data = st.session_state.analyzer
        new_analyzer = MarketAnalyzer()
        new_analyzer.cliente_data = getattr(old_data, 'cliente_data', {})
        new_analyzer.mercado_categoria = getattr(old_data, 'mercado_categoria', {})
        new_analyzer.mercado_subcategorias = getattr(old_data, 'mercado_subcategorias', {})
        st.session_state.analyzer = new_analyzer
        st.toast("🔄 Sistema atualizado para nova versão", icon="ℹ️")

# --- LÓGICA DE IMPORTAÇÃO EXCEL ---

def processar_excel(file):
    try:
        # Criar novo analyzer temporário
        temp_analyzer = MarketAnalyzer()
        
        # 1. Cliente
        df_cliente = pd.read_excel(file, sheet_name="Cliente", header=None)
        
        # Tentar localizar as linhas pelo nome na primeira coluna (mais robusto)
        def get_val_by_label(labels, default=""):
            if isinstance(labels, str): labels = [labels]
            for i in range(len(df_cliente)):
                cell_val = str(df_cliente.iloc[i, 0]).strip().lower()
                for label in labels:
                    if label.lower() in cell_val:
                        return df_cliente.iloc[i, 1]
            return default

        empresa = str(get_val_by_label(["Empresa", "Nome"], "Empresa Exemplo"))
        cat_macro_cliente = str(get_val_by_label(["Categoria Macro", "Macro"], "Geral"))
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
        
        # Mapeamento flexível de colunas
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
        
        # ATUALIZAÇÃO CRÍTICA: Substituir o objeto na sessão
        st.session_state.analyzer = temp_analyzer
        st.session_state['data_version'] = datetime.now().timestamp()
        
        # Feedback detalhado
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

# --- CSS CUSTOMIZADO ---
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem; font-weight: bold; color: #FFFFFF; background-color: #1E1E1E;
        text-align: center; padding: 1.5rem; border-radius: 0.5rem; margin-bottom: 2rem; border-bottom: 4px solid #3498db;
    }
    .metric-card {
        background-color: #262730; padding: 1.2rem; border-radius: 0.5rem; border-top: 3px solid #3498db; text-align: center;
    }
    .metric-label { font-size: 0.85rem; color: #A0A0A0; margin-bottom: 0.3rem; }
    .metric-value { font-size: 1.2rem; font-weight: bold; color: #FFFFFF; }
    .insight-card {
        background-color: #1E1E1E; padding: 1.5rem; border-radius: 0.5rem; border-left: 5px solid #3498db; margin-bottom: 1rem;
    }
    .insight-title { font-size: 1.1rem; font-weight: bold; margin-bottom: 0.5rem; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### 🧭 Navegação")
    menu = st.radio("Escolha a seção:", ["🏠 Início", "👤 Dados do Cliente", "📈 Gestão de Categorias", "🎯 Mercado Subcategorias", "📊 Dashboard Executivo"])
    
    st.markdown("---")
    st.markdown("### 📤 Importar Dados")
    
    uploaded_file = st.file_uploader("Suba sua planilha Excel", type=["xlsx"], key="excel_uploader_v5")
    if uploaded_file is not None:
        if st.button("🚀 Processar Planilha", use_container_width=True):
            if processar_excel(uploaded_file):
                st.success("Dados carregados!")
                st.rerun()
    
    if 'last_upload_info' in st.session_state:
        st.info(st.session_state.last_upload_info)
    
    st.markdown("---")
    st.markdown("### 📄 Gerar Relatório Executivo")

    # Usar st.session_state.analyzer para evitar NameError
    current_analyzer = st.session_state.analyzer

    if st.button("Gerar Relatório PDF", use_container_width=True, key="pdf_button"):
        if current_analyzer.cliente_data and (current_analyzer.mercado_categoria or current_analyzer.mercado_subcategoria):
            with st.spinner("Gerando seu relatório... Por favor, aguarde."):
                # Lógica para selecionar a categoria e subcategoria de foco para o relatório
                cat_foco = st.session_state.get("selected_macro_cat", "")
                sub_foco = st.session_state.get("selected_sub_cat_foco", "")
                
                if cat_foco and sub_foco:
                    # Obter a row_foco completa do ranking, que contém todos os dados necessários
                    df_ranking_completo = current_analyzer.gerar_ranking(cat_foco)
                    if not df_ranking_completo.empty and sub_foco in df_ranking_completo["Subcategoria"].values:
                        row_foco = df_ranking_completo[df_ranking_completo["Subcategoria"] == sub_foco].iloc[0].to_dict()
                    else:
                        row_foco = {"Categoria Macro": cat_foco, "Subcategoria": sub_foco, "Score": 0, "Status": "N/A", "Leitura": "N/A", "Ticket Cliente": current_analyzer.cliente_data.get("ticket_medio", 0)} # Fallback mais robusto
                else:
                    # Fallback: usar a primeira categoria/subcategoria disponível de forma segura
                    cat_foco = ""
                    sub_foco = ""
                    row_foco = {}
                    
                    if current_analyzer.mercado_subcategorias:
                        cat_foco = list(current_analyzer.mercado_subcategorias.keys())[0]
                        if current_analyzer.mercado_subcategorias[cat_foco]:
                            sub_foco = current_analyzer.mercado_subcategorias[cat_foco][0]['subcategoria']
                            df_ranking_completo = current_analyzer.gerar_ranking(cat_foco)
                            if not df_ranking_completo.empty:
                                row_foco = df_ranking_completo[df_ranking_completo["Subcategoria"] == sub_foco].iloc[0].to_dict()

                # Usar os valores do session_state para garantir que o PDF reflita a seleção do dashboard
                pdf = PDFReportGenerator(current_analyzer, current_analyzer.cliente_data, st.session_state.get("selected_macro_cat", ""), st.session_state.get("selected_sub_cat_foco", ""), row_foco)
                pdf_file_path = "relatorio_executivo.pdf"
                pdf.generate_report(pdf_file_path)

                with open(pdf_file_path, "rb") as f:
                    st.session_state.pdf_report = f.read()
                st.session_state.pdf_ready = True
                st.success("Relatório pronto para download!")
        else:
            st.warning("Por favor, importe os dados e selecione uma categoria no dashboard antes de gerar o relatório.")

    if st.session_state.get("pdf_ready"):
        st.download_button(
            label="📥 Download Relatório PDF",
            data=st.session_state.pdf_report,
            file_name="relatorio_executivo.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    st.markdown("---")
    st.markdown("### 📥 Exportar Dados")
    
    # Usar st.session_state.analyzer para evitar NameError
    current_analyzer = st.session_state.analyzer
    
    if current_analyzer.cliente_data or current_analyzer.mercado_categoria:
        # Criar Excel em memória
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Aba Cliente
            if current_analyzer.cliente_data:
                # Criar um formato similar ao template
                cliente_rows = [
                    ["", ""], ["", ""], ["", ""], ["", ""],
                    ["Empresa", current_analyzer.cliente_data.get('empresa', '')],
                    ["Categoria Macro", current_analyzer.cliente_data.get('categoria_principal', '')],
                    ["Ticket Médio Geral", current_analyzer.cliente_data.get('ticket_medio', 0)],
                    ["Margem Atual", current_analyzer.cliente_data.get('margem', 0)],
                    ["Faturamento Médio 3M", current_analyzer.cliente_data.get('faturamento_3m', 0)],
                    ["Unidades Médias 3M", current_analyzer.cliente_data.get('unidades_3m', 0)],
                    ["Range Permitido", current_analyzer.cliente_data.get('range_permitido', 0.20)],
                    ["Ticket Customizado", current_analyzer.cliente_data.get('ticket_custom', "")]
                ]
                pd.DataFrame(cliente_rows).to_excel(writer, sheet_name="Cliente", index=False, header=False)
            
            # Aba Mercado Categoria
            cat_data = []
            for cat, periods in current_analyzer.mercado_categoria.items():
                for p in periods:
                    cat_data.append({
                        "Categoria": cat,
                        "Periodo (texto)": p['periodo'],
                        "Faturamento (R$)": p['faturamento'],
                        "Unidades": p['unidades']
                    })
            if cat_data:
                # Criar DataFrame e escrever a partir da linha 3 (startrow=2) para manter o cabeçalho do template
                df_cat_export = pd.DataFrame(cat_data)
                df_cat_export.to_excel(writer, sheet_name="Mercado_Categoria", index=False, startrow=2)
            else:
                # Se estiver vazio, criar apenas o cabeçalho na linha 3
                pd.DataFrame(columns=["Categoria", "Periodo (texto)", "Faturamento (R$)", "Unidades"]).to_excel(writer, sheet_name="Mercado_Categoria", index=False, startrow=2)
            
            # Aba Mercado Subcategoria
            sub_data = []
            for cat, subs in current_analyzer.mercado_subcategorias.items():
                for s in subs:
                    sub_data.append({
                        "Categoria": cat,
                        "Subcategoria": s['subcategoria'],
                        "Faturamento 6M (R$)": s['faturamento_6m'],
                        "Unidades 6M": s['unidades_6m']
                    })
            if sub_data:
                # Criar DataFrame e escrever a partir da linha 3 (startrow=2)
                df_sub_export = pd.DataFrame(sub_data)
                df_sub_export.to_excel(writer, sheet_name="Mercado_Subcategoria", index=False, startrow=2)
            else:
                # Se estiver vazio, criar apenas o cabeçalho na linha 3
                pd.DataFrame(columns=["Categoria", "Subcategoria", "Faturamento 6M (R$)", "Unidades 6M"]).to_excel(writer, sheet_name="Mercado_Subcategoria", index=False, startrow=2)
        
        st.download_button(
            label="📥 Baixar Planilha Atualizada",
            data=output.getvalue(),
            file_name=f"Analise_Mercado_{current_analyzer.cliente_data.get('empresa', 'Empresa')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    st.markdown("---")
    if st.button("🗑️ Limpar Tudo (Zerar)", use_container_width=True, type="secondary"):
        st.session_state.analyzer = MarketAnalyzer()
        if 'last_upload_info' in st.session_state: del st.session_state['last_upload_info']
        st.rerun()

# Header
st.markdown('<div class="main-header">📊 Tamanho do Mercado</div>', unsafe_allow_html=True)

# Referência curta para o analyzer da sessão
analyzer = st.session_state.analyzer

# ====================
# SEÇÃO: INÍCIO
# ====================
if menu == "🏠 Início":
    st.markdown("## 🎯 Bem-vindo")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        ### 🚀 Como usar?
        1. **Importe seu Excel**: Use o campo na barra lateral para subir sua planilha preenchida.
        2. **Ajuste Manual**: Se precisar, altere os dados nas abas de Cliente, Categorias ou Subcategorias.
        3. **Analise**: Vá para o Dashboard Executivo para ver o ranking e os cenários.
        """)
    with col2:
        st.info("💡 **Dica**: O sistema agora aceita o modelo de planilha que você já utiliza, facilitando a migração dos dados!")
        
    if not analyzer.cliente_data:
        st.warning("⚠️ Nenhum dado carregado. Suba uma planilha na barra lateral para começar.")
    else:
        st.success(f"✅ Dados carregados para: **{analyzer.cliente_data.get('empresa', 'Empresa')}**")

# ====================
# SEÇÃO: DADOS DO CLIENTE
# ====================
elif menu == "👤 Dados do Cliente":
    st.markdown("## 👤 Dados do Cliente")
    ver = st.session_state.get('data_version', 0)
    
    st.info("💡 **Dica:** Você pode digitar valores como '1.5M' para 1 milhão e meio ou '500k' para 500 mil nos campos de faturamento e unidades.")
    
    with st.form("form_cliente"):
        col1, col2 = st.columns(2)
        with col1:
            empresa = st.text_input("Nome da Empresa", value=analyzer.cliente_data.get('empresa', ''), placeholder="Ex: Minha Empresa LTDA", key=f"emp_{ver}")
            ticket_medio = st.number_input("Ticket Médio Geral (R$)", min_value=0.0, value=float(analyzer.cliente_data.get('ticket_medio', 0.0)), format="%.2f", help="Ex: 150.00", key=f"tm_{ver}")
            margem = st.number_input("Margem Atual (%)", min_value=0.0, max_value=100.0, value=float(analyzer.cliente_data.get('margem', 0.0) * 100), step=0.1, help="Ex: 15.5 para 15,5%", key=f"mg_{ver}")
        with col2:
            fat_val = analyzer.cliente_data.get('faturamento_3m', 0.0)
            fat_input = st.text_input("Faturamento Médio 3M (R$)", value=str(fat_val) if fat_val > 0 else "", placeholder="Ex: 1.2M ou 1200000", key=f"fat_{ver}")
            uni_val = analyzer.cliente_data.get('unidades_3m', 0)
            uni_input = st.text_input("Unidades Médias 3M", value=str(uni_val) if uni_val > 0 else "", placeholder="Ex: 5000 ou 5k", key=f"uni_{ver}")
            range_permitido = st.number_input("Range de Preço Permitido (±%)", min_value=0.0, max_value=100.0, value=float(analyzer.cliente_data.get('range_permitido', 0.20) * 100), help="Variação aceitável entre seu preço e o mercado (Padrão: 20%)", key=f"rp_{ver}")
        
        st.markdown("#### 🚀 Dados de Performance (Opcional - Melhora a Precisão)")
        col3, col4 = st.columns(2)
        with col3:
            cac = st.text_input("CAC Médio (R$)", value=str(analyzer.cliente_data.get('cac', 0.0)), help="Custo de Aquisição de Cliente (Ex: 25.50)", key=f"cac_{ver}")
        with col4:
            invest_mkt = st.text_input("Investimento Mkt Mensal (R$)", value=str(analyzer.cliente_data.get('investimento_mkt', 0.0)), help="Quanto você investe hoje (Ex: 5000)", key=f"imkt_{ver}")

        if st.form_submit_button("💾 Salvar Dados"):
            fat_val_parsed = parse_large_number(fat_input)
            st.session_state.analyzer.set_cliente_data(
                empresa=empresa, categoria="Geral", ticket_medio=ticket_medio,
                margem=margem, faturamento_3m=fat_val_parsed, 
                unidades_3m=int(parse_large_number(uni_input)), range_permitido=range_permitido,
                cac=parse_large_number(cac), investimento_mkt=parse_large_number(invest_mkt)
            )
            # Garantir persistência absoluta do faturamento para os cálculos
            st.session_state.analyzer.cliente_data['faturamento_3m'] = fat_val_parsed
            st.session_state.analyzer.cliente_data['faturamento_medio_3m'] = fat_val_parsed
            
            st.session_state['data_version'] = datetime.now().timestamp()
            st.toast("✅ Dados salvos!", icon="💾")
            st.rerun()

# ====================
# SEÇÃO: GESTÃO DE CATEGORIAS
# ====================
elif menu == "📈 Gestão de Categorias":
    st.markdown("## 📈 Categorias Macro")
    with st.expander("➕ Adicionar Nova Categoria Macro"):
        with st.form("nova_cat"):
            nova_cat = st.text_input("Nome da Categoria")
            col1, col2, col3 = st.columns(3)
            periodo = col1.text_input("Período (ex: Jan/24)")
            fat_cat = col2.text_input("Faturamento Mercado (R$)")
            uni_cat = col3.text_input("Unidades Mercado")
            if st.form_submit_button("Adicionar"):
                if nova_cat:
                    analyzer.add_mercado_categoria(nova_cat, periodo, parse_large_number(fat_cat), int(parse_large_number(uni_cat)))
                    st.rerun()

    if analyzer.mercado_categoria:
        for cat in list(analyzer.mercado_categoria.keys()):
            df_cat = analyzer.get_mercado_categoria_df(cat).copy()
            if not df_cat.empty:
                col_title, col_actions = st.columns([4, 1])
                col_title.markdown(f"### 📂 {cat}")
                
                with col_actions:
                    if st.button(f"🗑️ Excluir Categoria", key=f"del_cat_{cat}"):
                        analyzer.remover_mercado_categoria(cat)
                        st.rerun()
                
                # Edição de Períodos
                with st.expander(f"📝 Editar Dados de {cat}"):
                    for i, row in df_cat.iterrows():
                        with st.form(f"edit_cat_{cat}_{i}"):
                            st.markdown(f"**Período: {row['periodo']}**")
                            c1, c2, c3 = st.columns(3)
                            new_name = c1.text_input("Nome Categoria", value=cat)
                            new_fat = c2.text_input("Faturamento (R$)", value=str(row['faturamento']))
                            new_uni = c3.text_input("Unidades", value=str(row['unidades']))
                            b1, b2 = st.columns(2)
                            if b1.form_submit_button("💾 Salvar"):
                                analyzer.editar_mercado_categoria(cat, new_name, row['periodo'], parse_large_number(new_fat), int(parse_large_number(new_uni)))
                                st.rerun()
                            if b2.form_submit_button("🗑️ Excluir Período", type="secondary"):
                                analyzer.remover_periodo_categoria(cat, row['periodo'])
                                st.rerun()

                # Métricas da Categoria
                m_col1, m_col2 = st.columns(2)
                fat_medio = df_cat['faturamento'].mean()
                tm_medio = df_cat['ticket_medio'].mean()
                m_col1.metric("Faturamento Médio", f"R$ {format_br(fat_medio)}")
                m_col2.metric("Ticket Médio", f"R$ {format_br(tm_medio)}")
                
                # Tabela de Dados
                df_disp = df_cat.copy()
                df_disp['faturamento'] = df_disp['faturamento'].apply(format_br)
                df_disp['ticket_medio'] = df_disp['ticket_medio'].apply(format_br)
                st.dataframe(df_disp, use_container_width=True)
                
                # Visualizações da Categoria
                st.markdown("#### 📈 Visualizações")
                tab1, tab2 = st.tabs(["Evolução da Categoria", "Ticket Médio"])
                with tab1:
                    st.plotly_chart(criar_grafico_evolucao_categoria(df_cat), use_container_width=True)
                with tab2:
                    st.plotly_chart(criar_grafico_ticket_medio(df_cat), use_container_width=True)
                st.markdown("---")
    else:
        st.info("Nenhuma categoria macro cadastrada.")

# ====================
# SEÇÃO: SUBCATEGORIAS
# ====================
elif menu == "🎯 Mercado Subcategorias":
    st.markdown("## 🎯 Subcategorias")
    categorias = list(analyzer.mercado_categoria.keys())
    if not categorias:
        st.warning("Cadastre uma Categoria Macro primeiro!")
    else:
        cat_sel = st.selectbox("Selecione a Categoria Macro:", categorias)
        with st.form("nova_sub"):
            sub = st.text_input("Nome da Subcategoria")
            col1, col2 = st.columns(2)
            fat_6m = col1.text_input("Faturamento 6M (R$)")
            uni_6m = col2.text_input("Unidades 6M")
            if st.form_submit_button("Adicionar Subcategoria"):
                if sub:
                    analyzer.add_mercado_subcategoria(cat_sel, sub, parse_large_number(fat_6m), int(parse_large_number(uni_6m)))
                    st.rerun()
        
        # ATUALIZAÇÃO: Garantir que as subcategorias sejam lidas corretamente do analyzer
        # Usar o objeto 'analyzer' que já está sincronizado com o session_state
        if cat_sel in analyzer.mercado_subcategorias:
            subcategorias_lista = analyzer.mercado_subcategorias[cat_sel]
            
            st.markdown("### 📋 Lista de Subcategorias")
            if not subcategorias_lista:
                st.info("Nenhuma subcategoria cadastrada para esta categoria macro.")
            else:
                df_sub_raw = pd.DataFrame(subcategorias_lista)
                
                # Tabela de visualização rápida
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
# SEÇÃO: DASHBOARD
# ====================
elif menu == "📊 Dashboard Executivo":
    st.markdown("## 📊 Dashboard Executivo")
    df_ranking = analyzer.gerar_ranking()
    if df_ranking.empty:
        st.info("Importe ou adicione dados para visualizar o dashboard.")
    else:
        col_rank1, col_rank2 = st.columns([1, 1])
        with col_rank1:
            st.markdown("### 🏆 Ranking de Oportunidades")
            df_display = df_ranking[['Categoria Macro', 'Subcategoria', 'Score', 'Status']].copy()
            st.dataframe(df_display, use_container_width=True)
        with col_rank2:
            st.plotly_chart(criar_grafico_ranking_subcategorias(df_ranking), use_container_width=True)
            
        st.markdown("---")
        # Garantir que a subcategoria selecionada seja salva no session_state
        sub_foco_dashboard = st.selectbox("Análise Detalhada da Subcategoria:", df_ranking["Subcategoria"].tolist(), key="dashboard_sub_foco_selector")
        st.session_state["selected_sub_cat_foco"] = sub_foco_dashboard
        
        # Encontrar a categoria macro correspondente à subcategoria selecionada
        row_foco = df_ranking[df_ranking["Subcategoria"] == sub_foco_dashboard].iloc[0]
        st.session_state["selected_macro_cat"] = row_foco["Categoria Macro"]
        
        # Seção de Simulação Interativa
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
            
            # Obter resultados da simulação
            res = analyzer.simular_cenarios(row_foco['Categoria Macro'], sub_foco_dashboard, custom_shares)
            
            # Cards de Indicadores Principais
            st.markdown("#### 📈 Indicadores de Market Share")
            m1, m2, m3, m4, m5 = st.columns(5)
            
            # Recalcular share atual
            share_atual_calc = analyzer.calcular_share_atual(res['mercado_6m'])
            
            with m1:
                st.markdown(f"""<div class="metric-card"><div class="metric-label">Tamanho Mercado (6M)</div><div class="metric-value">R$ {format_br(res['mercado_6m'])}</div></div>""", unsafe_allow_html=True)
            with m2:
                st.markdown(f"""<div class="metric-card"><div class="metric-label">Seu Share Atual</div><div class="metric-value">{share_atual_calc:.2f}%</div></div>""", unsafe_allow_html=True)
            with m3:
                # Share Alvo baseado no cenário Provável
                share_alvo = custom_shares['Provável']['share_alvo'] * 100
                st.markdown(f"""<div class="metric-card" style="border-top-color: #f1c40f;"><div class="metric-label">Meta de Share (Provável)</div><div class="metric-value">{share_alvo:.1f}%</div></div>""", unsafe_allow_html=True)
            with m4:
                st.markdown(f"""<div class="metric-card"><div class="metric-label">Ticket Médio Mercado</div><div class="metric-value">R$ {format_br(res['ticket_mercado'])}</div></div>""", unsafe_allow_html=True)
            with m5:
                st.markdown(f"""<div class="metric-card"><div class="metric-label">Sua Margem</div><div class="metric-value">{analyzer.cliente_data.get('margem', 0)*100:.1f}%</div></div>""", unsafe_allow_html=True)         
            # Gráficos de Score e Ticket
            g1, g2 = st.columns(2)
            with g1: st.plotly_chart(criar_gauge_score(row_foco['Score'], row_foco['Status']), use_container_width=True)
            with g2:
                r_perm = analyzer.cliente_data.get('range_permitido', 0.20)
                l_inf, l_sup = calcular_limites_ticket_local(res['ticket_mercado'], r_perm)
                st.plotly_chart(criar_comparacao_tickets(res['ticket_mercado'], row_foco['Ticket Cliente'], l_inf, l_sup), use_container_width=True)
            
            # Tabela e Gráfico de Cenários
            st.markdown("#### 📈 Projeções de Receita e Lucro")
            df_cen = res['cenarios'].copy()
            
            c_tab1, c_tab2 = st.tabs(["Tabela de Dados", "Gráfico Comparativo"])
            with c_tab1:
                df_disp_cen = df_cen.copy()
                
                # Função para colorir valores
                def color_delta(val):
                    color = '#2ecc71' if val > 0 else ('#e74c3c' if val < 0 else '#A0A0A0')
                    return f'color: {color}; font-weight: bold'

                # Aplicar formatação ao dataframe
                styled_df = df_disp_cen.style.applymap(color_delta, subset=['Delta vs Atual', 'Crescimento (%)'])
                
                # Formatação de exibição
                df_disp_cen['Receita Projetada 6M'] = df_disp_cen['Receita Projetada 6M'].apply(format_br)
                df_disp_cen['Lucro Projetado 6M'] = df_disp_cen['Lucro Projetado 6M'].apply(format_br)
                df_disp_cen['Delta vs Atual'] = df_disp_cen['Delta vs Atual'].apply(format_br)
                df_disp_cen['Crescimento (%)'] = df_disp_cen['Crescimento (%)'].apply(lambda x: f"{x:,.1f}%".replace(",", "X").replace(".", ",").replace("X", "."))
                
                st.dataframe(df_disp_cen, use_container_width=True)
            with c_tab2:
                st.plotly_chart(criar_grafico_cenarios(df_cen), use_container_width=True)
            
            # SEÇÃO DE TENDÊNCIA E PROJEÇÃO
            st.markdown("---")
            st.markdown("### 📈 Tendência e Projeção de Demanda")
            
            # Cálculo de Confiabilidade
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
                st.metric("Tendência Atual", tendencia_res['tendencia'], 
                          delta=f"{tendencia_res['crescimento_mensal']:.1f}% mensal")
            with t_col2:
                st.metric("Projeção Total (3 Meses)", f"R$ {format_br(tendencia_res['projecao_3m'])}")
            with t_col3:
                # Gráfico de Projeção Mensal
                meses = ["Mês 1", "Mês 2", "Mês 3"]
                valores = tendencia_res.get('mensal', [0, 0, 0])
                df_proj = pd.DataFrame({"Mês": meses, "Faturamento": valores})
                
                fig_proj = px.bar(df_proj, x="Mês", y="Faturamento", 
                                 text=[f"R$ {format_br(v)}" for v in valores],
                                 title="Projeção Mensal Detalhada",
                                 color_discrete_sequence=["#3498db"])
                fig_proj.update_traces(textposition='outside')
                fig_proj.update_layout(height=250, margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig_proj, use_container_width=True)

            # SEÇÃO DE PLANO DE AÇÃO
            st.markdown("---")
            st.markdown("### 🧠 Plano de Ação Sugerido")
            plano = analyzer.gerar_plano_acao(row_foco['Categoria Macro'])
            # Filtrar apenas para a subcategoria em foco para ser mais específico
            sub_plano = next((p for p in plano if p['Subcategoria'] == sub_foco_dashboard), None)
            
            if sub_plano:
                # Trava de segurança para compatibilidade entre versões (KeyError: 'Ações')
                lista_acoes = sub_plano.get('Ações', [])
                if not lista_acoes and 'Recomendação' in sub_plano:
                    lista_acoes = [sub_plano['Recomendação']]
                
                acoes_html = "".join([f"<li style='margin-bottom: 8px;'>{acao}</li>" for acao in lista_acoes])
                
                st.markdown(f"""
                <div class="insight-card" style="border-left-color: {sub_plano.get('Cor', '#3498db')}; background-color: #1E1E1E; padding: 20px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                        <span style="font-size: 1.3rem; font-weight: bold; color: {sub_plano.get('Cor', '#3498db')};">🎯 Prioridade: {sub_plano.get('Prioridade', 'N/A')}</span>
                        <span style="background-color: {sub_plano.get('Cor', '#3498db')}; color: white; padding: 4px 12px; border-radius: 15px; font-size: 0.9rem; font-weight: bold;">Score: {sub_plano.get('Score', 0):.2f}</span>
                    </div>
                    <ul style="list-style-type: none; padding-left: 0; font-size: 1.1rem; color: #E0E0E0;">
                        {acoes_html}
                    </ul>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.warning("Não foi possível gerar recomendações para esta subcategoria.")

            # SEÇÃO DE INSIGHTS
            st.markdown("### 💡 Insights dos Cenários")
            
            # Verificação de segurança para o faturamento base
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
