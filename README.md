<div align="center">

# 📊 Mercado Livre Ads Dashboard

### Dashboard Interativo e Inteligente para Análise e Otimização de Campanhas

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.0+-FF4B4B.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-success.svg)](https://github.com/vlima-creator/MelieADs)

---

</div>

## 🚀 Sobre o Projeto

Uma solução completa para análise e otimização de campanhas de publicidade no **Mercado Livre Ads**. Este dashboard oferece insights em tempo real, recomendações automáticas e um plano estratégico de 15 dias baseado no algoritmo do Mercado Livre.

---

## ✨ Funcionalidades Principais

### 📈 **KPIs em Tempo Real**
Acompanhe as métricas mais importantes da sua operação:
- 💰 **Investimento Total** em Ads
- 💵 **Receita Gerada** pelas campanhas
- 📊 **ROAS** (Return on Ad Spend)
- 🎯 **TACOS** (Total Advertising Cost of Sales)

### 📊 **Análise Visual de Performance**
Visualizações poderosas para tomada de decisão:
- **Gráfico de Pareto** → Identifica as campanhas "Locomotivas" que geram 80% da receita
- **Treemap de Alocação** → Visualiza a distribuição de investimento por campanha e quadrante

### 🗓️ **Plano de Ação Estratégico (15 Dias)**
Metodologia baseada no algoritmo do Mercado Livre:
- **Semana 1**: Ajustes ativos (escala, pausar, reduzir ROAS objetivo)
- **Semana 2**: Período de aprendizado - sem alterações nas campanhas ajustadas
- ⏱️ Respeita a janela de **7 dias** do algoritmo para máxima eficiência

### 🤖 **Recomendações Automáticas**
O sistema analisa e sugere ações:
- ⛔ **Pausar/Revisar** → Campanhas com alto investimento e baixa performance
- 🎯 **Entrar em Ads** → Produtos orgânicos com alta conversão prontos para publicidade
- 📈 **Escalar Orçamento** → Campanhas com ROAS forte e perda por orçamento
- 🎚️ **Baixar ROAS Objetivo** → Campanhas com alta perda por classificação

### 🔍 **Matriz CPI**
Análise avançada de oportunidades de otimização baseada em **Cost Per Impression**.

---

## 🛠️ Instalação e Uso

### 📋 **Requisitos**
- Python 3.8 ou superior
- Relatórios do Mercado Livre em formato Excel:
  - ✅ Relatório de Desempenho de Vendas (Orgânico)
  - ✅ Relatório de Anúncios Patrocinados
  - ✅ Relatório de Campanha

### 💻 **Instalação Local**

```bash
# 1. Clonar o repositório
git clone https://github.com/vlima-creator/MelieADs.git
cd MelieADs

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Executar o dashboard
streamlit run app.py
```

### 🌐 **Acesso Online**
> 🔗 Deploy em produção: [Link será fornecido após deploy]

---

## ⚙️ Configuração de Filtros

Personalize os critérios de análise no dashboard:

| Filtro | Descrição | Valor Padrão |
|--------|-----------|--------------|
| **Visitas Mínimas** | Número mínimo de visitas para considerar produto | 50 |
| **Conversão Mínima** | Taxa mínima de conversão para entrar em Ads | 3,00% |
| **Investimento Mínimo** | Investimento mínimo para considerar pausar | R$ 20,00 |
| **CVR Máximo** | Taxa de conversão máxima antes de pausar | 1,50% |

> 💡 **Dica**: Os valores padrão são baseados em boas práticas do mercado, mas podem ser ajustados conforme sua operação.

---

## 📊 Estrutura de Dados Esperada

### 📄 **Relatório de Desempenho de Vendas**
- ID do anúncio
- Título
- Visitas
- Quantidade de Vendas
- Vendas Brutas
- Conversão (Visitas → Vendas)

### 📄 **Relatório de Anúncios Patrocinados**
- Código do anúncio
- Impressões
- Cliques
- Receita
- Investimento
- ROAS

### 📄 **Relatório de Campanha**
- Nome da Campanha
- Status
- Orçamento
- ACOS Objetivo
- Impressões
- Cliques
- Receita
- Investimento
- Vendas

---

## 🎯 Interpretação dos Quadrantes

O sistema classifica automaticamente as campanhas em 4 quadrantes estratégicos:

| Quadrante | Descrição | Ação Recomendada |
|-----------|-----------|------------------|
| 🚀 **Escala de Orçamento** | ROAS forte + alta perda por orçamento | Aumentar investimento |
| 🎯 **Competitividade** | Alta perda por classificação | Reduzir ROAS objetivo |
| ❌ **Hemorragia** | ROAS baixo ou negativo | Pausar ou revisar drasticamente |
| ✅ **Estável** | Performance dentro dos parâmetros | Manter monitoramento |

---

## 📅 Metodologia: Plano de 15 Dias

### 🧠 **Por que 7 dias?**
O algoritmo do Mercado Livre Ads precisa de **7 dias** para sair do modo de aprendizado após uma alteração. Alterações frequentes quebram esse ciclo e prejudicam a performance.

### 📆 **Estrutura Recomendada**

#### **Dias 1-7: Ajustes Ativos** 🔧
- **Dia 1**: Escala de orçamento + Pausar hemorragias
- **Dia 3**: Reduzir ROAS objetivo (competitividade)
- **Dia 5**: Monitoramento

#### **Dias 8-15: Período de Aprendizado** 🧘
- ⏸️ Não altere as campanhas ajustadas
- 👀 Apenas monitore ROAS, CPC e volume
- 📝 Prepare próximas otimizações
- **Dia 15**: Reavaliação e planejamento do próximo ciclo

---

## 📈 Métricas Principais

### 💰 **ROAS (Return on Ad Spend)**
```
ROAS = Receita / Investimento
```
> **Meta**: Acima de **5x**  
> Quanto maior, melhor. Indica o retorno de cada real investido.

### 🎯 **TACOS (Total Advertising Cost of Sales)**
```
TACOS = Investimento Ads / Faturamento Total
```
> **Meta**: Abaixo de **15%**  
> Quanto menor, melhor. Mostra o peso dos Ads no faturamento total.

### 📊 **ACOS (Advertising Cost of Sales)**
```
ACOS = Investimento / Receita Ads
```
> Quanto menor, melhor. É o inverso do ROAS.

### 🔄 **CVR (Conversion Rate)**
```
CVR = Vendas / Cliques
```
> Percentual de cliques que resultam em venda.

---

## 🔧 Tecnologias Utilizadas

<div align="center">

| Tecnologia | Função |
|------------|--------|
| ![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white) | Framework para dashboards interativos |
| ![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white) | Processamento e análise de dados |
| ![Plotly](https://img.shields.io/badge/Plotly-3F4F75?style=for-the-badge&logo=plotly&logoColor=white) | Visualizações gráficas interativas |
| ![Python](https://img.shields.io/badge/Python_3.11-3776AB?style=for-the-badge&logo=python&logoColor=white) | Linguagem de programação |

</div>

---

## 🔐 Segurança e Privacidade

- 🏠 **Processamento Local**: Os dados são processados localmente
- 🚫 **Zero Armazenamento**: Nenhum dado é armazenado em servidores externos
- 🔒 **Execução Independente**: Cada execução é isolada e segura

---

## 🐛 Troubleshooting

### ❓ **"Arquivo de estilo não encontrado"**
Certifique-se de que o diretório `.streamlit/` existe e contém o arquivo `style.css`.

### ❓ **"Erro ao processar os arquivos"**
Verifique se os arquivos Excel estão no formato correto e contêm todas as colunas esperadas.

### ❓ **Gráficos não aparecem**
Verifique se a biblioteca Plotly está instalada:
```bash
pip install plotly
```

---

## 📞 Suporte e Contato

Para dúvidas, sugestões ou suporte técnico, entre em contato com a equipe de desenvolvimento.

---

## 📝 Changelog

### 🆕 **v2.0 (Atual)**
- ✅ Gráficos de Pareto e Treemap
- ✅ Plano de 15 dias com trava de 7 dias
- ✅ UI/UX melhorada com tema escuro
- ✅ Filtros de regra customizáveis

### 📦 **v1.0**
- Análise básica de campanhas
- Recomendações automáticas
- Plano de 7 dias

---

## 📄 Licença

**Propriedade de Rafa Consulting**. Todos os direitos reservados.

---

<div align="center">

**Última atualização**: Janeiro de 2026

⭐ **Se este projeto foi útil, considere dar uma estrela!** ⭐

</div>
