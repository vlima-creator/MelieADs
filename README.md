# 📊 Mercado Livre Ads - Dashboard e Relatório

Um dashboard interativo e inteligente para análise e otimização de campanhas de publicidade no Mercado Livre Ads.

## 🎯 Funcionalidades Principais

### 1. **KPIs em Tempo Real**
- Investimento total em Ads
- Receita gerada
- ROAS (Return on Ad Spend)
- TACOS (Total Advertising Cost of Sales)

### 2. **Análise Visual de Performance**
- **Gráfico de Pareto**: Identifica as campanhas "Locomotivas" que geram 80% da receita
- **Treemap de Alocação**: Visualiza a distribuição de investimento por campanha e quadrante

### 3. **Plano de Ação Estratégico (15 Dias)**
- **Semana 1**: Ajustes ativos (escala, pausar, reduzir ROAS objetivo)
- **Semana 2**: Período de aprendizado - sem alterações nas campanhas ajustadas
- Respeita a janela de 7 dias do algoritmo do Mercado Livre para máxima eficiência

### 4. **Recomendações Automáticas**
- **Pausar/Revisar**: Campanhas com alto investimento e baixa performance
- **Entrar em Ads**: Produtos orgânicos com alta conversão prontos para publicidade
- **Escalar Orçamento**: Campanhas com ROAS forte e perda por orçamento
- **Baixar ROAS Objetivo**: Campanhas com alta perda por classificação

### 5. **Matriz CPI**
Análise de oportunidades de otimização com base em CPI (Cost Per Impression)

## 📋 Como Usar

### Requisitos
- Python 3.8+
- Relatórios do Mercado Livre em formato Excel:
  - Relatório de Desempenho de Vendas (Orgânico)
  - Relatório de Anúncios Patrocinados
  - Relatório de Campanha

### Instalação Local

```bash
# Clonar o repositório
git clone https://github.com/Rafaconsulting/ml-ads-relatorio-teste.git
cd ml-ads-relatorio-teste

# Instalar dependências
pip install -r requirements.txt

# Executar o dashboard
streamlit run app.py
```

### Uso Online
Acesse o dashboard permanente em: [Link será fornecido após deploy]

## 🎚️ Filtros de Regra

Customize os critérios de análise:

- **Entrar em Ads (Visitas mín)**: Número mínimo de visitas para considerar um produto
- **Entrar em Ads (Conversão mín %)**: Taxa mínima de conversão
- **Pausar (Investimento mín R$)**: Investimento mínimo para considerar pausar
- **Pausar (CVR máx %)**: Taxa de conversão máxima antes de pausar

**Valores padrão recomendados:**
- Visitas: 50
- Conversão: 3,00%
- Investimento: R$ 20,00
- CVR: 1,50%

## 📊 Estrutura de Dados

### Colunas Esperadas

#### Relatório de Desempenho de Vendas
- ID do anúncio
- Título
- Visitas
- Quantidade de Vendas
- Vendas Brutas
- Conversão (Visitas → Vendas)

#### Relatório de Anúncios Patrocinados
- Código do anúncio
- Impressões
- Cliques
- Receita
- Investimento
- ROAS

#### Relatório de Campanha
- Nome da Campanha
- Status
- Orçamento
- ACOS Objetivo
- Impressões
- Cliques
- Receita
- Investimento
- Vendas

## 🔍 Interpretação dos Quadrantes

O sistema classifica automaticamente as campanhas em quadrantes:

- **🚀 Escala de Orçamento**: ROAS forte + alta perda por orçamento → aumentar investimento
- **🎯 Competitividade**: Alta perda por classificação → reduzir ROAS objetivo
- **❌ Hemorragia**: ROAS baixo ou negativo → pausar ou revisar drasticamente
- **✅ Estável**: Performance dentro dos parâmetros → manter monitoramento

## 📅 Plano de 15 Dias - Metodologia

### Por que 7 dias?
O algoritmo do Mercado Livre Ads precisa de 7 dias para sair do modo de aprendizado após uma alteração. Alterações frequentes quebram esse ciclo.

### Estrutura Recomendada

**Dias 1-7: Ajustes Ativos**
- Dia 1: Escala de orçamento + Pausar hemorragias
- Dia 3: Reduzir ROAS objetivo (competitividade)
- Dia 5: Monitoramento

**Dias 8-15: Período de Aprendizado**
- Não altere as campanhas ajustadas
- Apenas monitore ROAS, CPC e volume
- Prepare próximas otimizações
- Dia 15: Reavaliação e planejamento do próximo ciclo

## 🛠️ Tecnologias Utilizadas

- **Streamlit**: Framework para dashboards interativos
- **Pandas**: Processamento e análise de dados
- **Plotly**: Visualizações gráficas interativas
- **Python 3.11**: Linguagem de programação

## 📈 Métricas Principais

### ROAS (Return on Ad Spend)
```
ROAS = Receita / Investimento
```
Quanto maior, melhor. Meta: acima de 5x.

### TACOS (Total Advertising Cost of Sales)
```
TACOS = Investimento Ads / Faturamento Total
```
Quanto menor, melhor. Meta: abaixo de 15%.

### ACOS (Advertising Cost of Sales)
```
ACOS = Investimento / Receita Ads
```
Quanto menor, melhor. Inverso do ROAS.

### CVR (Conversion Rate)
```
CVR = Vendas / Cliques
```
Percentual de cliques que resultam em venda.

## 🔐 Segurança e Privacidade

- Os dados são processados localmente
- Nenhum dado é armazenado em servidores externos
- Cada execução é independente

## 🐛 Troubleshooting

### "Arquivo de estilo não encontrado"
Certifique-se de que o diretório `.streamlit/` existe e contém o arquivo `style.css`.

### "Erro ao processar os arquivos"
Verifique se os arquivos Excel estão no formato correto e contêm todas as colunas esperadas.

### Gráficos não aparecem
Verifique se a biblioteca Plotly está instalada: `pip install plotly`

## 📞 Suporte

Para dúvidas ou sugestões, entre em contato com a equipe de desenvolvimento.

## 📝 Changelog

### v2.0 (Atual)
- ✅ Gráficos de Pareto e Treemap
- ✅ Plano de 15 dias com trava de 7 dias
- ✅ UI/UX melhorada com tema escuro
- ✅ Filtros de regra customizáveis

### v1.0
- Análise básica de campanhas
- Recomendações automáticas
- Plano de 7 dias

## 📄 Licença

Propriedade de Rafa Consulting. Todos os direitos reservados.

---

**Última atualização**: Janeiro de 2026
