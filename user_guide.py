
import streamlit as st

def render_user_guide():
    st.title("📖 Guia de Uso - Dashboard Estratégico")
    st.write("Este guia explica como utilizar o dashboard, quais relatórios são necessários, como configurar os parâmetros e como os cálculos são realizados.")

    with st.expander("Como Começar - Passo a Passo", expanded=True):
        st.markdown("""
        Para começar a usar o Dashboard Estratégico, siga estes passos:

        1.  **Selecione o Marketplace:** Na barra lateral esquerda, escolha entre **Mercado Livre** ou **Shopee**.
        2.  **Faça Upload dos Relatórios:** Para cada marketplace, faça o upload dos arquivos de relatório obrigatórios e opcionais conforme indicado na seção "Localizando os Relatórios".
        3.  **Ajuste os Filtros de Regra:** Defina os parâmetros para as regras de entrada e pausa de anúncios, bem como as regras por anúncio (Ads).
        4.  **Gere o Relatório:** Clique no botão "Gerar relatório" para processar os dados e visualizar o dashboard.
        5.  **Analise os Dados:** Explore as diferentes abas e seções do dashboard para obter insights sobre suas campanhas.
        """)

    with st.expander("Localizando os Relatórios", expanded=False):
        st.markdown("""
        ### 📦 Mercado Livre

        Para o Mercado Livre, você precisará dos seguintes relatórios:

        *   **Relatório de Desempenho de Anúncios (Excel):**
            *   **Caminho:** Métricas > Selecionar o Período > Descer até a sessão Desempenho de anúncios > Baixar relatório > Desempenho dos seus anúncios.
            *   **Conteúdo:** Detalha a performance orgânica de cada anúncio.

        *   **Relatório Anúncios Patrocinados (Excel):**
            *   **Caminho:** Publicidade > Relatórios > Tipo de Relatório: Anúncios (Padrão) > Selecionar Período > Agrupamento de Dados: Total do Período.
            *   **Conteúdo:** Detalha a performance de cada anúncio dentro do Ads.

        *   **Relatório de Campanha (Excel):**
            *   **Caminho:** Publicidade > Relatórios > Tipo de Relatório: Campanhas (Padrão) > Selecionar Período > Agrupamento de Dados: Total do Período.
            *   **Conteúdo:** Traz o resumo consolidado das suas campanhas.

        *   **Snapshot de Referência (Excel) - Opcional:**
            *   **Caminho:** Gerado automaticamente pelo dashboard na primeira execução ou baixado manualmente.
            *   **Conteúdo:** Arquivo gerado há 15 dias para comparar evolução (Snapshot v2).

        *   **Arquivo de Estoque (Excel) - Opcional:**
            *   **Caminho:** Arquivo personalizado com informações de estoque.
            *   **Conteúdo:** Utilizado para ativar a visão de estoque e aplicar regras baseadas na disponibilidade.

        ### 🛒 Shopee

        Para a Shopee, você precisará dos seguintes relatórios:

        *   **Dados Gerais de Anúncios (CSV) - Obrigatório:**
            *   **Caminho:** Central do Vendedor > Marketing > Meus Anúncios > Relatórios > Selecionar Período > Tipo de Relatório: Todos os Anúncios CPC > Exportar.
            *   **Conteúdo:** Relatório de Todos os Anúncios CPC da Shopee.

        *   **Relatório de Palavras-chave (CSV) - Opcional:**
            *   **Caminho:** Central do Vendedor > Marketing > Meus Anúncios > Relatórios > Selecionar Período > Tipo de Relatório: Anúncio + Palavra-chave + Locação > Exportar.
            *   **Conteúdo:** Detalha a performance das palavras-chave nos seus anúncios.
        """)

    with st.expander("O que você encontra em cada Aba", expanded=False):
        st.markdown("""
        O dashboard é dividido em seções principais para facilitar a análise:

        ### 📊 Indicadores Chave de Performance (KPIs)
        *   **Mercado Livre:** Investimento, Receita, ROAS e TACOS.
        *   **Shopee:** GMV Total, Despesas, ROAS Médio, ROAS Direto Médio, Crédito Proteção Total e Campanhas com Proteção.

        ### 📈 Análise Visual de Performance
        *   **Mercado Livre:** Gráficos de Pareto e Treemap para análise de campanhas.
        *   **Shopee:** Análise de Proteção de ROAS, Conversões Diretas vs Totais e Recomendações Estratégicas (Ativar Proteção, Otimizar ROAS, Escalar GMV, Pausar/Revisar).

        ### 📋 Painel Geral de Campanhas
        *   **Mercado Livre:** Tabela detalhada com informações de campanhas, incluindo migração de quadrantes e ações recomendadas.

        ### 📉 Matriz CPI (Oportunidades de Otimização)
        *   **Mercado Livre:** Tabela para identificar oportunidades de otimização de campanhas.

        ### 🎯 Nível de Anúncio (Patrocinados)
        *   **Mercado Livre:** Análise tática por anúncio, anúncios para pausar, anúncios vencedores, otimização de fotos, otimização de palavras-chave e otimização de oferta.
        """)

    with st.expander("Explicação dos Cálculos e Métricas", expanded=False):
        st.markdown("""
        Aqui estão as definições e fórmulas dos principais indicadores utilizados no dashboard:

        ### Indicadores Gerais

        *   **ROAS (Return On Ad Spend):** Retorno sobre o investimento em publicidade.
            *   **Fórmula:** `(Receita de Vendas Gerada por Anúncios / Investimento em Anúncios)`
            *   **Interpretação:** Quanto maior, melhor. Indica quantos reais de receita são gerados para cada real investido em anúncios.

        *   **TACOS (Total Advertising Cost of Sales):** Custo total de publicidade sobre as vendas totais.
            *   **Fórmula:** `(Investimento em Anúncios / Vendas Totais)`
            *   **Interpretação:** Quanto menor, melhor. Indica a porcentagem das vendas totais que é gasta em publicidade.

        *   **CTR (Click-Through Rate):** Taxa de cliques.
            *   **Fórmula:** `(Cliques / Impressões) * 100`
            *   **Interpretação:** A porcentagem de pessoas que viram seu anúncio e clicaram nele.

        *   **CVR (Conversion Rate):** Taxa de conversão.
            *   **Fórmula:** `(Vendas / Cliques) * 100`
            *   **Interpretação:** A porcentagem de pessoas que clicaram no seu anúncio e realizaram uma compra.

        ### Indicadores Shopee Específicos

        *   **GMV Total (Gross Merchandise Volume):** Valor bruto total das mercadorias vendidas.
            *   **Fórmula:** `Soma de todas as vendas`
            *   **Interpretação:** Mede o volume total de vendas na plataforma.

        *   **Despesas:** Custo total com publicidade na Shopee.
            *   **Fórmula:** `Soma de todos os gastos com anúncios`
            *   **Interpretação:** O valor total investido em campanhas de anúncios.

        *   **ROAS Médio:** ROAS calculado com base no GMV total e despesas totais.
            *   **Fórmula:** `(GMV Total / Despesas)`
            *   **Interpretação:** Retorno médio do investimento em anúncios na Shopee.

        *   **ROAS Direto Médio:** ROAS calculado com base nas conversões diretas e despesas.
            *   **Fórmula:** `(Receita de Conversões Diretas / Despesas)`
            *   **Interpretação:** Retorno do investimento considerando apenas as vendas atribuídas diretamente aos anúncios.

        *   **Crédito Proteção Total:** Valor potencial de crédito a ser recebido pela Shopee por campanhas que não atingiram o ROAS alvo.
            *   **Fórmula:** `(ROAS Alvo - ROAS Real) * Despesas` (para campanhas elegíveis)
            *   **Interpretação:** Indica o valor que pode ser recuperado em campanhas com baixo desempenho, conforme as políticas de proteção da Shopee.
        """)

    with st.expander("Dicas e Boas Práticas", expanded=False):
        st.markdown("""
        *   **Atualize seus relatórios regularmente:** Para ter os dados mais precisos, baixe e faça o upload dos relatórios com frequência.
        *   **Monitore as recomendações:** Fique atento às sugestões do dashboard para otimizar suas campanhas e proteger seu ROAS.
        *   **Experimente os filtros:** Utilize os filtros de regra para simular diferentes cenários e encontrar a melhor estratégia para seus anúncios.
        *   **Compare com o Snapshot V2 (Mercado Livre):** Use o recurso de snapshot para acompanhar a evolução de suas campanhas ao longo do tempo.
        *   **Entenda suas métricas:** Familiarize-se com os KPIs e suas fórmulas para tomar decisões mais assertivas.
        """)
