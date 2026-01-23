# 📊 Análise da Shopee - Notas de Implementação

## 🎯 Objetivo
Expandir o dashboard MelieADs para suportar análise de múltiplos marketplaces, começando com a Shopee.

---

## 📄 Estrutura dos Relatórios da Shopee

### **Relatório 1: Dados Gerais de Anúncios**
**Colunas (31):**
1. Nome do Anúncio
2. Status
3. Tipos de Anúncios
4. ID do produto
5. Criativo
6. Método de Lance
7. Posicionamento
8. Data de Início
9. Data de Encerramento
10. **Impressões**
11. **Cliques**
12. **CTR**
13. **Conversões**
14. **Conversões Diretas**
15. **Taxa de Conversão**
16. **Taxa de Conversão Direta**
17. **Custo por Conversão**
18. **Custo por Conversão Direta**
19. **Itens Vendidos**
20. **Itens Vendidos Diretos**
21. **GMV** ⭐ (Métrica principal)
22. **Receita direta**
23. **Despesas**
24. **ROAS** ⭐
25. **ROAS Direto** ⭐
26. **ACOS**
27. **ACOS Direto**
28. Impressões do Produto
29. Cliques de Produtos
30. CTR do Produto

### **Relatório 2: Anúncio + Palavra-chave + Locação**
**Colunas adicionais (33):**
- Palavra-chave/Localização
- Tipo de combinação
- (Mesmas métricas do Relatório 1)

---

## 🎯 GMV Max - Proteção de ROAS

### **O que é?**
Sistema de **proteção automática** da Shopee que oferece **crédito de anúncios gratuitos** quando o ROAS real cai abaixo do ROAS alvo definido.

### **Como Funciona:**

#### **Qualificação para Proteção:**
Para usar a Proteção de ROAS, produtos devem ser promovidos usando **GMV Max Meta de ROAS**.

**Critérios de Conversão Diária:**
| Tipo de Campanha | Mínimo de Conversões Diárias |
|------------------|------------------------------|
| GMV Max de item único | ≥ 5 conversões |
| Grupo de Anúncios | ≥ 5 conversões |
| GMV Max da Loja | ≥ 10 conversões |

#### **Taxa de Cumprimento de ROAS:**
```
Taxa de Cumprimento = ROAS Real ÷ ROAS Alvo
```
(Para cliques atribuídos aos anúncios)

**Limites:**
| Condição | Atingimento Mínimo |
|----------|-------------------|
| Campanhas Padrão | < 90% |
| Campanhas com "Impulsão Rápida" | < 70% |

---

### **Cálculo do Crédito Elegível:**

#### **Campanhas Padrão:**
```
Crédito = Despesas - (GMV de anúncios ÷ (ROAS alvo × 90%))
```

#### **Campanhas com Impulsão Rápida:**
```
Crédito = Despesas - (GMV de anúncios ÷ (ROAS alvo × 70%))
```

**Condição:** Se GMV amplo > 0

---

### **Condições de Saída da Proteção:**

| Condição | Regra | Reingresso |
|----------|-------|-----------|
| **Atividade Fraudulenta** | Sistema detecta comportamento fraudulento | Produtos elegíveis após 14 dias da saída |
| **Ajuste de Meta de ROAS** | Ajuste manual da meta | Elegível após ajuste |
| **Alteração de Status** | Pausar/interromper campanhas GMV Max | Elegível no dia seguinte ao reinício |

---

## 📊 Métricas Principais da Shopee

### **KPIs Essenciais:**
1. **GMV (Gross Merchandise Value)** - Valor bruto de mercadoria
2. **ROAS** - Return on Ad Spend
3. **ROAS Direto** - ROAS de conversões diretas
4. **ACOS** - Advertising Cost of Sales
5. **Despesas** - Investimento em anúncios
6. **Receita Direta** - Receita atribuída diretamente aos anúncios
7. **Conversões** - Total de conversões
8. **Conversões Diretas** - Conversões atribuídas diretamente
9. **Taxa de Conversão**
10. **CTR** - Click-Through Rate

### **Diferenças vs Mercado Livre:**
| Aspecto | Mercado Livre | Shopee |
|---------|---------------|--------|
| **Métrica Principal** | Receita Ads | GMV |
| **Proteção** | Não tem | Proteção de ROAS |
| **ROAS** | Calculado | Direto + Total |
| **Conversões** | Vendas | Conversões + Diretas |
| **Crédito** | Não tem | Crédito automático |

---

## 🏗️ Arquitetura Multi-Marketplace

### **Estrutura Proposta:**

```
MelieADs/
├── app.py (main)
├── ml_report.py (Mercado Livre)
├── shopee_report.py (Shopee) ← NOVO
├── marketplace_selector.py ← NOVO
├── liquid_glass_components.py
└── .streamlit/
    └── style.css
```

### **Fluxo de Navegação:**

1. **Sidebar**: Seletor de Marketplace
   - 🛒 Mercado Livre
   - 🛍️ Shopee
   - (Futuro: Amazon, Magazine Luiza, etc.)

2. **Upload de Arquivos**: Dinâmico por canal
   - **Mercado Livre**: 3 relatórios (Vendas, Patrocinados, Campanha)
   - **Shopee**: 2 relatórios (Dados Gerais, Palavra-chave)

3. **Análise**: Específica por marketplace
   - KPIs customizados
   - Gráficos adaptados
   - Recomendações contextualizadas

---

## 🎯 Implementação - Checklist

### **Fase 1: Estrutura Base**
- [ ] Criar módulo `marketplace_selector.py`
- [ ] Criar módulo `shopee_report.py`
- [ ] Refatorar `app.py` para suportar múltiplos canais

### **Fase 2: Análise Shopee**
- [ ] Parser de relatórios CSV da Shopee
- [ ] Cálculo de KPIs (GMV, ROAS, ACOS)
- [ ] Análise de Proteção de ROAS
- [ ] Identificação de campanhas elegíveis
- [ ] Cálculo de crédito potencial

### **Fase 3: Interface**
- [ ] Seletor de canal no sidebar
- [ ] Upload dinâmico de arquivos
- [ ] Cards KPI adaptados (GMV, ROAS Direto)
- [ ] Gráficos específicos da Shopee
- [ ] Tabela de campanhas com proteção

### **Fase 4: Recomendações**
- [ ] Campanhas para ativar Proteção de ROAS
- [ ] Campanhas com baixo cumprimento de ROAS
- [ ] Oportunidades de otimização de GMV
- [ ] Análise de conversões diretas vs totais

---

## 📋 Campos Importantes para Análise

### **Obrigatórios:**
- Nome do Anúncio
- Status
- Tipos de Anúncios
- Método de Lance
- GMV
- Receita direta
- Despesas
- ROAS
- ROAS Direto
- Conversões
- Conversões Diretas

### **Opcionais (para análise avançada):**
- Palavra-chave/Localização
- Posicionamento
- CTR
- Taxa de Conversão
- Custo por Conversão

---

## 🎨 UI/UX - Adaptações

### **Cards KPI para Shopee:**
1. 💰 **GMV Total**
2. 💵 **Despesas**
3. 📈 **ROAS Médio**
4. 🎯 **ROAS Direto**
5. 🛡️ **Crédito de Proteção** (novo)

### **Seções Específicas:**
- 🛡️ **Status de Proteção de ROAS**
- 📊 **Análise de GMV por Campanha**
- 🎯 **Conversões Diretas vs Totais**
- 💰 **Crédito Elegível Calculado**

---

## 🔄 Próximos Passos

1. ✅ Analisar arquivos da Shopee
2. ✅ Entender GMV Max e Proteção de ROAS
3. ⏳ Projetar arquitetura multi-marketplace
4. ⏳ Implementar seletor de canal
5. ⏳ Criar módulo de análise Shopee
6. ⏳ Integrar no dashboard
7. ⏳ Testar e validar

---

**Data**: 23/01/2026  
**Fonte**: Relatórios Shopee + PDF "Fique por dentro da Proteção de ROAS do GMV Max"


---

## 🔍 Identificação de Campanhas com Proteção de ROAS

### **Na Lista de Anúncios:**
- Filtro disponível: "Show Ads in ROAS Protection Only"
- Tag verde "ROAS Protection" indica status válido
- Tag vermelha indica status inválido (condição de saída)

### **Na Página de Detalhes do Anúncio:**
- Seção "ROAS Protection" mostra:
  - **Total Rebate Amount**: Valor total de reembolso
  - **Rebate Details**: Histórico de descontos diários
- Botão "Detalhes do Desconto" expande informações

### **Na Página "Minha Conta":**
- Tipo de transação: **"Proteção ROAS"**
- Registra pagamentos de reembolso
- Aparece em:
  - "Carteira de Anúncios"
  - "Crédito de Anúncios Gratuitos"
- Histórico de transações com filtro específico

---

## 💰 Crédito de Anúncios Gratuitos

### **Visualização:**
- **Account Balance**: Saldo total de créditos
- **Free Ads Credit**: Crédito gratuito disponível
- **Applicable Ad Types**: Tipos de anúncios elegíveis
- **Valid Period**: Período de validade
- **Received Date**: Data de recebimento

### **Origem:**
- "ROAS Protection Rebate" (Reembolso da Proteção de ROAS)
- Crédito distribuído no dia seguinte (geralmente)
- Pode haver atrasos em períodos promocionais

---

## ❓ Perguntas Frequentes

### **Proteção de ROAS vs Pagamento por Venda:**
- Proteção de ROAS **substitui** o modelo de Pagamento por Venda
- Objetivo: Entrega mais confiável e experiência aprimorada

---

## 🎯 Implementação no Dashboard - Funcionalidades Específicas

### **1. Identificador de Proteção Ativa**
- Badge/Tag visual para campanhas com proteção
- Status: Ativo ✅ / Inativo ❌
- Motivo de inativação (se aplicável)

### **2. Calculadora de Crédito Elegível**
```python
def calcular_credito_protecao(gmv, despesas, roas_alvo, impulsao_rapida=False):
    """
    Calcula o crédito elegível da Proteção de ROAS
    """
    if gmv <= 0:
        return 0
    
    percentual = 0.70 if impulsao_rapida else 0.90
    credito = despesas - (gmv / (roas_alvo * percentual))
    
    return max(0, credito)  # Não pode ser negativo
```

### **3. Monitor de Taxa de Cumprimento**
```python
def taxa_cumprimento_roas(roas_real, roas_alvo):
    """
    Calcula a taxa de cumprimento de ROAS
    """
    if roas_alvo == 0:
        return 0
    return (roas_real / roas_alvo) * 100
```

### **4. Alertas de Elegibilidade**
- ⚠️ Campanha próxima de perder proteção (< 95% cumprimento)
- ✅ Campanha elegível para proteção
- ❌ Campanha fora dos critérios

### **5. Histórico de Créditos**
- Tabela com reembolsos recebidos
- Total acumulado no período
- Projeção de crédito futuro

---

## 📊 KPIs Exclusivos da Shopee

### **Métricas de Proteção:**
1. **Crédito Total Recebido** (R$)
2. **Campanhas com Proteção Ativa** (#)
3. **Taxa Média de Cumprimento** (%)
4. **Crédito Projetado** (R$)
5. **Economia com Proteção** (R$)

### **Análise de Conversões:**
1. **Conversões Totais** vs **Conversões Diretas**
2. **GMV Total** vs **Receita Direta**
3. **ROAS Total** vs **ROAS Direto**
4. **Taxa de Conversão** vs **Taxa de Conversão Direta**

---

## 🎨 Cards KPI Shopee (Atualizado)

```python
kpis_shopee = [
    {
        "icon": "💰",
        "label": "GMV TOTAL",
        "value": "R$ 50.000,00"
    },
    {
        "icon": "💵",
        "label": "DESPESAS",
        "value": "R$ 10.000,00"
    },
    {
        "icon": "📈",
        "label": "ROAS MÉDIO",
        "value": "5,00x"
    },
    {
        "icon": "🎯",
        "label": "ROAS DIRETO",
        "value": "4,50x"
    },
    {
        "icon": "🛡️",
        "label": "CRÉDITO PROTEÇÃO",
        "value": "R$ 1.200,00"
    },
    {
        "icon": "✅",
        "label": "CAMPANHAS PROTEGIDAS",
        "value": "12"
    }
]
```

---

**Atualizado em**: 23/01/2026  
**Páginas analisadas do PDF**: 1-10 de 27
