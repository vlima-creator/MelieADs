"""
Componentes visuais com efeito Liquid Glass (Glassmorphism)
Estilo minimalista inspirado em designs modernos
"""

import streamlit as st


def render_glass_kpi_card(icon, label, value, container_class="glass-kpi-card"):
    """
    Renderiza um card KPI com efeito Liquid Glass
    
    Args:
        icon: Ícone minimalista (emoji ou unicode)
        label: Texto do label (ex: "TOTAL DE ANÚNCIOS")
        value: Valor a ser exibido (ex: "2.004" ou "R$ 898.340,70")
        container_class: Classe CSS customizada
    """
    html = f"""
    <div class="{container_class}">
        <div class="glass-icon">{icon}</div>
        <div class="glass-label">{label}</div>
        <div class="glass-value">{value}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def inject_glass_kpi_styles():
    """
    Injeta estilos CSS para os cards KPI com efeito Liquid Glass
    Deve ser chamado uma vez no início do app
    """
    css = """
    <style>
    /* ========================================
       GLASS KPI CARDS - Liquid Glass Effect
       ======================================== */
    .glass-kpi-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 24px 20px;
        box-shadow: 
            0 8px 32px 0 rgba(0, 0, 0, 0.37),
            inset 0 1px 0 0 rgba(255, 255, 255, 0.05);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        text-align: left;
        min-height: 140px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    
    .glass-kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 
            0 12px 48px 0 rgba(0, 0, 0, 0.5),
            inset 0 1px 0 0 rgba(255, 255, 255, 0.1);
        border-color: rgba(255, 255, 255, 0.15);
    }
    
    .glass-icon {
        width: 48px;
        height: 48px;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        margin-bottom: 16px;
    }
    
    .glass-label {
        color: rgba(255, 255, 255, 0.7);
        font-size: 0.75rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-bottom: 8px;
    }
    
    .glass-value {
        color: #ffffff;
        font-size: 1.75rem;
        font-weight: 600;
        letter-spacing: -0.5px;
        line-height: 1.2;
    }
    
    /* Responsividade */
    @media (max-width: 768px) {
        .glass-kpi-card {
            min-height: 120px;
            padding: 20px 16px;
        }
        
        .glass-icon {
            width: 40px;
            height: 40px;
            font-size: 20px;
        }
        
        .glass-value {
            font-size: 1.5rem;
        }
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def render_glass_kpi_row(kpis_data):
    """
    Renderiza uma linha de KPIs com efeito Liquid Glass
    
    Args:
        kpis_data: Lista de dicionários com keys: icon, label, value
        Exemplo:
        [
            {"icon": "📦", "label": "TOTAL DE ANÚNCIOS", "value": "2.004"},
            {"icon": "💵", "label": "FATURAMENTO TOTAL", "value": "R$ 898.340,70"},
            {"icon": "📊", "label": "QUANTIDADE TOTAL", "value": "16.521"},
            {"icon": "🎯", "label": "TICKET MÉDIO", "value": "R$ 54,38"}
        ]
    """
    # Injeta estilos (idempotente)
    inject_glass_kpi_styles()
    
    # Cria colunas
    cols = st.columns(len(kpis_data))
    
    # Renderiza cada card
    for col, kpi in zip(cols, kpis_data):
        with col:
            render_glass_kpi_card(
                icon=kpi.get("icon", ""),
                label=kpi.get("label", ""),
                value=kpi.get("value", "")
            )


def render_glass_section_header(title, subtitle=None):
    """
    Renderiza um cabeçalho de seção com estilo Liquid Glass
    
    Args:
        title: Título da seção
        subtitle: Subtítulo opcional
    """
    html = f"""
    <div style="margin: 32px 0 24px 0;">
        <h2 style="
            color: #ffffff;
            font-weight: 300;
            letter-spacing: -0.5px;
            margin-bottom: 8px;
            font-size: 1.75rem;
        ">{title}</h2>
        {f'<p style="color: rgba(255, 255, 255, 0.6); font-size: 0.95rem; margin: 0;">{subtitle}</p>' if subtitle else ''}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
