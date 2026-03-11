
import streamlit as st

def render_user_guide():
    st.title("📖 Guia de Uso - Dashboard Estratégico MelieADs")
    st.write("Este guia detalha o funcionamento do dashboard, os indicadores apresentados, a origem dos dados e a lógica por trás de cada cálculo e recomendação.")

    with st.expander("🚀 Como Começar - Fluxo de Trabalho", expanded=True):
        st.markdown("""
        O MelieADs foi projetado para transformar relatórios brutos em decisões estratégicas. Siga o fluxo abaixo:

        1.  **Escolha o Canal:** Na barra lateral, selecione **Mercado Livre** ou **Shopee**.
        2.  **Upload de Dados:** Insira os arquivos exportados diretamente das plataformas (veja a seção "Localizando os Relatórios").
        3.  **Configuração de Regras:** 
            *   Defina o **ACOS Máximo** desejado.
            *   Ajuste as travas de **Estoque Mínimo** para evitar gastar em produtos sem disponibilidade.
            *   Configure os filtros de **Confiança de Dado** (investimento/cliques mínimos para gerar recomendação).
        4.  **Processamento:** Clique em **"Gerar relatório"**. O sistema irá cruzar os dados orgânicos com os de publicidade.
        5.  **Execução:** Utilize as tabelas de "Ações Recomendadas" para aplicar as mudanças diretamente na sua conta.
        """)

    with st.expander("📂 Localizando os Relatórios", expanded=False):
        st.markdown("""
        ### 🟡 Mercado Livre (Obrigatórios)
        *   **Desempenho de Anúncios (Orgânico):** 
            *   `Métricas > Anúncios > Baixar Relatório (Excel)`. 
            *   *Uso:* Base para cálculo de conversão orgânica e TACOS.
        *   **Anúncios Patrocinados (Ads):** 
            *   `Publicidade > Relatórios > Tipo: Anúncios > Agrupamento: Total`. 
            *   *Uso:* Performance individual de cada item em Ads.
        *   **Relatório de Campanha:** 
            *   `Publicidade > Relatórios > Tipo: Campanhas > Agrupamento: Total`. 
            *   *Uso:* Visão macro e perda de impressões.

        ### 🟠 Shopee (Obrigatórios)
        *   **Dados Gerais de Anúncios:** 
            *   `Central do Vendedor > Marketing > Meus Anúncios > Relatórios > Todos os Anúncios CPC > Exportar (CSV)`.
            *   *Uso:* Base para cálculo de GMV, ROAS e Proteção.

        ### 📎 Opcionais (Ambos)
        *   **Estoque:** Arquivo Excel com colunas `ITEM_ID` e `QUANTITY`.
        *   **Snapshot:** Arquivo gerado anteriormente pelo próprio MelieADs para análise de evolução (Antes vs Depois).
        """)

    with st.expander("📈 Indicadores e Fórmulas de Cálculo", expanded=False):
        st.markdown("""
        ### 📊 Indicadores Universais
        
        *   **ROAS Real (Return On Ad Spend):** Eficiência direta do investimento.
            *   **Cálculo:** `Receita Ads / Investimento Ads`
            *   *Exemplo:* ROAS 5.00x significa que cada R$ 1,00 investido gerou R$ 5,00 em vendas.
        
        *   **CTR (Click-Through Rate):** Atratividade do anúncio.
            *   **Cálculo:** `(Cliques / Impressões) * 100`
            *   *Benchmark:* Abaixo de 0.60% costuma indicar necessidade de revisão de foto ou título.

        *   **CVR (Conversion Rate):** Poder de venda da oferta.
            *   **Cálculo:** `(Vendas / Cliques) * 100`

        ### 🟡 Exclusivos Mercado Livre
        
        *   **TACOS (Total Advertising Cost of Sales):** Impacto do Ads no faturamento total.
            *   **Cálculo:** `Investimento Ads / Faturamento Total (Orgânico + Ads)`
            *   *Uso:* Mede a saúde financeira da conta. O ideal costuma ser entre 5% e 15%.
        
        *   **Perda por Orçamento:** % de vezes que seu anúncio parou de aparecer porque o dinheiro do dia acabou.
        *   **Perda por Classificação (Rank):** % de vezes que seu anúncio perdeu o leilão por falta de relevância ou ROAS alvo muito alto.

        ### 🟠 Exclusivos Shopee
        
        *   **Crédito Proteção Total:** Estimativa de reembolso da Shopee.
            *   **Cálculo:** `Despesas - (GMV / (ROAS Alvo * 0.90))`
            *   *Nota:* Se a "Impulsão Rápida" estiver ativa, o fator de proteção cai para 70% (0.70).
        
        *   **Qualidade de Atribuição:** % de vendas que são diretas vs. totais.
            *   **Cálculo:** `(Vendas Diretas / Vendas Totais) * 100`
        """)

    with st.expander("🎯 Lógica das Recomendações (Inteligência do App)", expanded=False):
        st.markdown("""
        O MelieADs utiliza uma **Matriz de Quadrantes** para classificar suas campanhas e anúncios:

        ### 🟡 Mercado Livre
        1.  **ESCALA (Escalar Orçamento):** 
            *   *Critério:* ROAS > 7.0 e Perda por Orçamento > 40%.
            *   *Ação:* Aumentar o orçamento diário para capturar a demanda reprimida.
        2.  **COMPETITIVIDADE (Baixar ROAS Alvo):** 
            *   *Critério:* Receita alta e Perda por Classificação > 50%.
            *   *Ação:* Reduzir o ROAS Alvo para ganhar mais leilões e volume.
        3.  **HEMORRAGIA (Pausar/Revisar):** 
            *   *Critério:* ROAS < 3.0 ou ACOS Real > 30% acima do objetivo.
            *   *Ação:* Pausar anúncios ineficientes ou reduzir lances drasticamente.

        ### 🟠 Shopee
        1.  **ATIVAR PROTEÇÃO:** ROAS < 2.5 com investimento > R$ 50.
        2.  **OTIMIZAR ROAS:** ROAS entre 2.5 e 3.0 com mais de 5 conversões.
        3.  **ESCALAR GMV:** ROAS > 4.0.
        """)

    with st.expander("🛡️ Regras de Estoque e Bloqueios", expanded=False):
        st.markdown("""
        Para evitar desperdício de verba, o app aplica filtros automáticos:
        
        *   **Bloqueio de Entrada:** Se um produto tem estoque abaixo do "Mínimo para entrar em Ads", ele não será recomendado para ativação, mesmo que tenha ótima conversão orgânica.
        *   **Freio de Segurança:** Campanhas com produtos em **Estoque Crítico** ou **Baixo** recebem o status "FREAR", priorizando a manutenção do estoque para vendas orgânicas orgânicas até a reposição.
        """)

    st.divider()
    st.info("💡 **Dica:** Utilize o botão de 'Baixar Excel' ao final da página para obter o plano de ação detalhado para levar para sua operação.")
