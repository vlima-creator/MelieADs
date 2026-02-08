# 📊 ANÁLISE COMPLETA DO TEMPLATE DE ANÁLISE DE MERCADO MARKETPLACE

## 🎯 VISÃO GERAL

Este é um **template Excel profissional** projetado para análise estratégica de mercado em marketplaces, focado em:
- Análise de viabilidade de categorias e subcategorias
- Dimensionamento de oportunidades de mercado
- Projeção de receita e lucratividade
- Tomada de decisão baseada em dados

---

## 📋 ESTRUTURA DO TEMPLATE (8 Abas)

### 1️⃣ **00_LEIA-ME** (Guia Inicial)
- **Propósito**: Orientações rápidas de uso
- **Conteúdo**: Instruções passo a passo para preenchimento
- **Público**: Primeiro contato para novos usuários

### 2️⃣ **README_USO** (Manual Detalhado)
- **Propósito**: Manual completo de uso da ferramenta
- **Conteúdo**:
  - Passo 1-5: Fluxo completo de preenchimento
  - Como interpretar cenários automáticos
  - Explicações sobre os indicadores

### 3️⃣ **Cliente** (Dados do Cliente)
**Campos para Preenchimento (em laranja):**
- ✏️ Nome da Empresa
- ✏️ Categoria macro (texto)
- ✏️ Ticket médio do cliente (R$)
- ✏️ Margem atual (%)
- ✏️ Faturamento médio (últimos 3 meses)
- ✏️ Unidades médias (últimos 3 meses)
- ✏️ Range permitido vs ticket do mercado (±%)
- ✏️ Ticket custom (opcional)

**Exemplo no Template:**
- Empresa: **Tamoyo**
- Categoria: **Ferramentas**
- Ticket médio: **R$ 204,34**
- Margem: **15%**
- Faturamento 3M: **R$ 33.511,65**
- Unidades 3M: **200**
- Range: **±20%**

**Inteligência da Aba:**
- Calcula ticket automaticamente se só informar faturamento e unidades
- Define limites de ticket aceitáveis para análise de fit

### 4️⃣ **Mercado_Categoria** (Visão Macro)
**Propósito**: Contexto histórico da categoria

**Estrutura de Dados:**
- Categoria
- Período (mês/ano)
- Faturamento (R$)
- Unidades
- Ticket médio (calculado automaticamente)

**Exemplo com Categoria "Ferramentas":**
```
Jan/2025: R$ 601.000 | 3.300 uni | R$ 182,12
Fev/2025: R$ 577.000 | 3.100 uni | R$ 186,13
Mar/2025: R$ 611.800 | 3.300 uni | R$ 185,39
Abr/2025: R$ 612.100 | 3.300 uni | R$ 185,48
Mai/2025: R$ 656.600 | 3.600 uni | R$ 182,39
Jun/2025: R$ 676.500 | 3.900 uni | R$ 173,46
```

**Uso Estratégico:**
- Identificar tendências (crescimento/queda)
- Sazonalidade da categoria
- Base para narrativa executiva

### 5️⃣ **Mercado_Subcategoria** (Detalhamento)
**Propósito**: Análise granular de subcategorias

**Campos:**
- Categoria
- Subcategoria
- Faturamento 6M (R$)
- Unidades 6M
- Ticket médio mercado (calculado)
- Score final (automático)
- Status (automático)
- Chave (identificação única)

**Exemplo Real do Template:**

| Subcategoria | Faturamento 6M | Unidades 6M | Ticket Médio | Score | Status |
|--------------|----------------|-------------|--------------|-------|--------|
| **Ferramentas Elétricas** | R$ 3,73 bi | 20,5 mi | R$ 181,95 | 1.0 | **FOCO** ✅ |
| Ferramentas Manuais | R$ 583,6 mi | 5,15 mi | R$ 113,32 | 0.23 | **EVITAR** ⚠️ |
| Acessórios p/ Ferramentas | R$ 555,6 mi | 6,0 mi | R$ 92,60 | 0.22 | **EVITAR** ⚠️ |

**Lógica do Score:**
- Combina tamanho de mercado + fit de ticket
- Normalizado de 0 a 1
- Score mais alto = maior prioridade

**Status Automáticos:**
- 🟢 **FOCO**: Melhor oportunidade (score alto)
- 🟡 **OK**: Oportunidade secundária
- 🔴 **EVITAR**: Não recomendado

### 6️⃣ **Ranking_Subcategorias** (Priorização)
**Propósito**: Ranking automático de oportunidades

**Colunas:**
- Subcategoria
- Mercado (R$) - volume 6M
- Ticket mercado
- Ticket cliente
- Score (0-1)
- Status (FOCO/OK/EVITAR)
- Leitura (diagnóstico)

**Diagnósticos Automáticos:**
- ✅ "Ticket OK" - Cliente está alinhado com mercado
- ⬇️ "Reduzir ticket" - Cliente precisa ajustar preço para baixo
- ⬆️ "Aumentar ticket" - Cliente pode subir preço

**Exemplo do Ranking:**
1. **Ferramentas Elétricas** - R$ 3,73bi - Score 1.0 - FOCO - "Ticket OK"
2. Ferramentas Manuais - R$ 583mi - Score 0.23 - EVITAR - "Reduzir ticket"
3. Acessórios - R$ 555mi - Score 0.22 - EVITAR - "Reduzir ticket"

### 7️⃣ **Dashboard** (Dashboard Executivo)
**Propósito**: Visão consolidada + simulações

**Seção 1: Seleção e Indicadores Chave**
- 🎯 Seletor de subcategoria foco
- 💰 Mercado 6M
- 🎫 Ticket mercado vs Ticket cliente
- 📊 Share atual (3M vs 6M)
- 💹 Margem atual
- ⭐ Score de prioridade
- 🚦 Status (FOCO/OK/EVITAR)

**Exemplo para "Ferramentas Elétricas":**
```
Mercado 6M: R$ 3.730.000.000
Ticket mercado: R$ 181,95
Ticket cliente: R$ 204,34
Fit ticket: DENTRO ✅
Share atual: 0,0018% (muito pequeno)
Margem: 0,15%
Status: FOCO
Score: 1.0
```

**Seção 2: Simulação de Ticket Custom**
- Campo para testar ticket alternativo
- Validação automática (dentro do range ±20%)
- Limite inferior: R$ 145,56
- Limite superior: R$ 218,34

**Seção 3: Cenários Automáticos**
Simula crescimento de participação no mercado:

| Cenário | Share Alvo | Ticket | Receita 6M | Lucro 6M | Delta vs Atual |
|---------|------------|--------|------------|----------|----------------|
| **Conservador** | 0,2% | R$ 204,34 | R$ 7.460.000 | R$ 11.190 | +R$ 7.392.976 |
| **Provável** | 0,5% | R$ 204,34 | R$ 18.650.000 | R$ 27.975 | +R$ 18.649.600 |
| **Otimista** | 1,0% | R$ 204,34 | R$ 37.300.000 | R$ 55.950 | +R$ 37.299.200 |

**Como funciona:**
- **Share Alvo**: % do mercado da subcategoria que cliente conquistará
- **Receita Projetada**: Mercado 6M × Share Alvo
- **Lucro Projetado**: Receita × Margem do cliente
- **Delta**: Incremento vs situação atual

### 8️⃣ **Cenarios** (Aba de Apoio)
- Espaço para detalhamentos mês a mês (se necessário)
- Cálculos auxiliares
- Atualmente com uso opcional

---

## 🧠 LÓGICA DE NEGÓCIO IDENTIFICADA

### 1. **Algoritmo de Score e Priorização**

**Fatores Considerados:**
1. **Tamanho de Mercado** (peso alto)
   - Quanto maior o faturamento 6M, maior o potencial
   
2. **Fit de Ticket** (peso médio-alto)
   - Compara ticket cliente vs ticket mercado
   - Considera o range permitido (±20% por padrão)
   - Penaliza desalinhamentos grandes

**Classificação:**
- Score = f(tamanho_mercado, fit_ticket)
- Normalização para escala 0-1
- Score 1.0 = melhor oportunidade identificada

**Status Resultante:**
- **FOCO**: Score mais alto + ticket dentro do range
- **OK**: Score médio + ticket aceitável
- **EVITAR**: Score baixo OU ticket muito desalinhado

### 2. **Cálculo de Share Atual**

```
Share = (Faturamento Médio 3M × 2) ÷ Mercado 6M
```

**Interpretação:**
- Estimativa conservadora de participação
- Multiplica por 2 para projetar de 3M para 6M
- Útil para entender ponto de partida

**Exemplo:**
```
Share = (R$ 33.511,65 × 2) ÷ R$ 3.730.000.000
Share = 0,0018% (muito pequeno, grande potencial)
```

### 3. **Validação de Ticket**

**Range Dinâmico:**
```
Limite Inferior = Ticket Mercado × (1 - Range%)
Limite Superior = Ticket Mercado × (1 + Range%)
```

**Com Range de 20%:**
```
Inferior = R$ 181,95 × 0,8 = R$ 145,56
Superior = R$ 181,95 × 1,2 = R$ 218,34
Cliente: R$ 204,34 → DENTRO ✅
```

### 4. **Projeção de Cenários**

**Fórmula Base:**
```
Receita Projetada 6M = Mercado 6M × Share Alvo
Lucro Projetado 6M = Receita × Margem Cliente
Delta = Receita Projetada - (Faturamento 3M × 2)
```

**Cenário Conservador (0,2%):**
```
Receita = R$ 3.730.000.000 × 0,002 = R$ 7.460.000
Lucro = R$ 7.460.000 × 0,0015 = R$ 11.190
Delta = R$ 7.460.000 - R$ 67.023,30 = R$ 7.392.976
```

---

## 🎯 CASOS DE USO IDENTIFICADOS

### **Caso de Uso Principal: Consultoria de Marketplace**

**Persona:** Consultor/Analista de e-commerce

**Fluxo de Trabalho:**

1. **Reunião com Cliente** → Coleta dados iniciais (Cliente)
2. **Pesquisa de Mercado** → Obtém dados de marketplace (Mercado_Categoria, Mercado_Subcategoria)
3. **Análise Automática** → Template calcula scores e rankings
4. **Seleção Estratégica** → Escolhe subcategoria FOCO no Dashboard
5. **Simulação de Cenários** → Mostra potencial de crescimento
6. **Apresentação Executiva** → Usa Dashboard para recomendações

### **Perguntas que o Template Responde:**

✅ Em qual subcategoria o cliente deve focar?
✅ O ticket do cliente está alinhado com o mercado?
✅ Qual o tamanho da oportunidade (em R$)?
✅ Quanto de receita/lucro pode gerar em diferentes cenários?
✅ Qual a participação de mercado atual e potencial?
✅ Vale a pena entrar neste mercado?

### **Decisões Suportadas:**

🎯 **Estratégicas:**
- Definir portfólio de categorias
- Priorizar investimentos
- Escolher batalhas competitivas

💰 **Financeiras:**
- Projetar receita e lucratividade
- Avaliar ROI de expansão
- Definir metas de share

🎫 **Táticas:**
- Ajustar precificação
- Adequar ticket médio
- Posicionar produtos

---

## 🔧 FUNCIONALIDADES TÉCNICAS

### **Automatizações Identificadas:**

1. **Cálculos Automáticos:**
   - Ticket médio (em múltiplas abas)
   - Score de priorização
   - Status (FOCO/OK/EVITAR)
   - Fit de ticket
   - Share atual
   - Projeções de cenários
   - Limites de ticket (inferior/superior)

2. **Validações:**
   - Ticket custom dentro do range permitido
   - Consistência de dados entre abas
   - Alertas visuais (cores)

3. **Formatação Condicional:**
   - Células em laranja = input do usuário
   - Verde (FOCO), Amarelo (OK), Vermelho (EVITAR)
   - Campos calculados em branco/cinza

4. **Dependências entre Abas:**
   ```
   Cliente → define ticket e margem
   ↓
   Mercado_Subcategoria → calcula score vs ticket cliente
   ↓
   Ranking_Subcategorias → ordena por score
   ↓
   Dashboard → permite seleção e simula cenários
   ```

---

## 💡 INSIGHTS ESTRATÉGICOS

### **Pontos Fortes do Template:**

✅ **Simplicidade**: Apenas células laranja para preencher
✅ **Automação**: Cálculos e rankings automáticos
✅ **Visual**: Dashboard executivo claro
✅ **Orientado a Decisão**: Status (FOCO/OK/EVITAR) direto
✅ **Simulação**: Cenários conservador/provável/otimista prontos
✅ **Fundamentado**: Combina tamanho de mercado + fit de ticket

### **Premissas do Modelo:**

1. **Dados de Mercado Confiáveis**: Requer acesso a dados de marketplace
2. **Período 6M**: Base de análise semestral
3. **Linear**: Projeções assumem crescimento linear de share
4. **Margem Constante**: Não considera variação de margem por subcategoria
5. **Ticket Estável**: Não simula mudanças de ticket ao longo do tempo (exceto campo custom)

### **Limitações Identificadas:**

⚠️ **Sazonalidade**: Não modela variações sazonais fortes
⚠️ **Competição**: Não considera ações de concorrentes
⚠️ **Custos de Aquisição**: Não inclui CAC ou custos de marketing para ganhar share
⚠️ **Ramp-up**: Assume share imediato, sem curva de crescimento
⚠️ **Mix de Produtos**: Trata subcategoria como homogênea

---

## 🎓 EXEMPLO PRÁTICO DE USO

### **Caso: Empresa Tamoyo (Ferramentas)**

**Situação Atual:**
- Faturamento 3M: R$ 33.511,65
- Ticket médio: R$ 204,34
- Margem: 15%
- Share atual: 0,0018% (quase nada)

**Análise de Subcategorias:**

| Subcategoria | Mercado 6M | Recomendação | Motivo |
|--------------|------------|--------------|--------|
| **Ferramentas Elétricas** | R$ 3,73 bi | **FOCO** ✅ | Mercado gigante + ticket OK |
| Ferramentas Manuais | R$ 583 mi | EVITAR ⚠️ | Ticket muito baixo (R$ 113) |
| Acessórios | R$ 555 mi | EVITAR ⚠️ | Ticket muito baixo (R$ 92) |

**Decisão:** Focar em **Ferramentas Elétricas**

**Potencial Identificado:**

🎯 **Cenário Conservador (0,2% share):**
- Receita 6M: R$ 7,46 milhões
- Crescimento: **111x** vs atual
- Lucro adicional: R$ 11.190

🎯 **Cenário Provável (0,5% share):**
- Receita 6M: R$ 18,65 milhões
- Crescimento: **278x** vs atual
- Lucro adicional: R$ 27.975

🎯 **Cenário Otimista (1,0% share):**
- Receita 6M: R$ 37,3 milhões
- Crescimento: **556x** vs atual
- Lucro adicional: R$ 55.950

**Recomendações Estratégicas:**
1. ✅ Manter ticket em R$ 204,34 (dentro do range aceitável)
2. ✅ Concentrar portfólio em Ferramentas Elétricas
3. ✅ Meta inicial: 0,2% de share (R$ 7,46mi/semestre)
4. ⚠️ Evitar Ferramentas Manuais e Acessórios (ticket muito baixo)

---

## 🚀 POSSÍVEIS MELHORIAS IDENTIFICADAS

### **Curto Prazo:**
1. Adicionar campo de CAC estimado
2. Incluir curva de ramp-up (crescimento gradual)
3. Gráficos visuais no Dashboard
4. Alertas para dados inconsistentes

### **Médio Prazo:**
1. Análise de concorrência (top players)
2. Sazonalidade mês a mês nos cenários
3. Sensibilidade de margem por subcategoria
4. ROI considerando investimentos necessários

### **Longo Prazo:**
1. Integração com APIs de marketplaces (dados em tempo real)
2. Machine Learning para prever share potencial
3. Análise de mix de produtos dentro da subcategoria
4. Benchmark de velocidade de crescimento do setor

---

## 📊 RESUMO EXECUTIVO

### **O que é:**
Template Excel para análise de oportunidades em marketplaces, com foco em priorização de categorias e projeção de crescimento.

### **Para quem:**
- Consultores de e-commerce
- Gestores de marketplace
- Analistas de expansão comercial
- Sellers que querem escalar

### **Diferencial:**
Combina simplicidade de uso com rigor analítico, gerando recomendações claras (FOCO/OK/EVITAR) baseadas em tamanho de mercado e fit de ticket.

### **Outputs Principais:**
1. Ranking de subcategorias priorizadas
2. Validação de adequação de ticket
3. Projeções de receita/lucro em 3 cenários
4. Dashboard executivo para apresentação

### **Valor Entregue:**
Transforma dados brutos de mercado em decisões estratégicas acionáveis, com quantificação de oportunidades e riscos.

---

## 📝 CONCLUSÃO DA ANÁLISE

Este template é uma **ferramenta de consultoria estratégica** extremamente bem estruturada. A lógica de negócio é sólida, com foco em:

✅ **Priorização baseada em dados** (tamanho de mercado + fit)
✅ **Simplicidade de uso** (poucos inputs, muitos insights)
✅ **Orientação a ação** (FOCO/OK/EVITAR é direto)
✅ **Quantificação de valor** (cenários com R$ e lucro)

O exemplo da **Tamoyo** em **Ferramentas Elétricas** ilustra perfeitamente o uso: cliente com ticket de R$ 204 consegue fit perfeito em mercado de R$ 3,7 bilhões, com potencial de crescimento de até **556x** (cenário otimista).

**Aplicações identificadas:**
- Due diligence de entrada em categorias
- Pitch para investidores (mostrando potencial)
- Planejamento comercial anual
- Avaliação de pivotagem estratégica
- Negociação com marketplaces (mostrando fit)

O template é **production-ready** e demonstra maturidade em consultoria de marketplace.
