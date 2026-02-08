# 🚀 GUIA RÁPIDO DE USO

## ⚡ Acesso Rápido

**URL da Aplicação:** https://8501-iop68hor4a5nswkx5ljlg-8f57ffe2.sandbox.novita.ai

**Repositório GitHub:** https://github.com/vlima-creator/Tamanho-do-Mercado

---

## 📋 Passo a Passo

### 1️⃣ DADOS DO CLIENTE (Obrigatório)

Acesse o menu **"👤 Dados do Cliente"** e preencha:

- ✅ **Empresa:** Nome do cliente
- ✅ **Categoria Macro:** Ex: "Ferramentas", "Eletrônicos", "Moda"
- ✅ **Ticket Médio:** Valor médio de venda (R$)
- ✅ **Margem:** Percentual de lucro (%)
- ✅ **Faturamento 3M:** Faturamento médio dos últimos 3 meses
- ✅ **Unidades 3M:** Quantidade vendida nos últimos 3 meses
- ⚙️ **Range Permitido:** Tolerância de variação de ticket (padrão: ±20%)

**💡 Exemplo:**
```
Empresa: Tamoyo
Categoria: Ferramentas
Ticket Médio: R$ 204,34
Margem: 15%
Faturamento 3M: R$ 33.511,65
Unidades 3M: 200
Range: ±20%
```

---

### 2️⃣ MERCADO CATEGORIA (Opcional)

Acesse **"📈 Mercado Categoria"** para adicionar histórico:

- Período (mês/ano)
- Faturamento total da categoria
- Unidades vendidas

**Objetivo:** Identificar tendências e sazonalidade

---

### 3️⃣ MERCADO SUBCATEGORIAS (Obrigatório)

Acesse **"🎯 Mercado Subcategorias"** e adicione **pelo menos 3 subcategorias**:

- Nome da subcategoria
- Faturamento dos últimos 6 meses
- Unidades vendidas dos últimos 6 meses

**💡 Exemplo:**
```
Subcategoria: Ferramentas Elétricas
Faturamento 6M: R$ 3.730.000.000
Unidades 6M: 20.500.000

Subcategoria: Ferramentas Manuais
Faturamento 6M: R$ 583.600.000
Unidades 6M: 5.150.000

Subcategoria: Acessórios para Ferramentas
Faturamento 6M: R$ 555.600.000
Unidades 6M: 6.000.000
```

**✨ A aplicação calculará automaticamente:**
- Score de priorização (0 a 1)
- Status (FOCO/OK/EVITAR)
- Fit de ticket
- Ranking de subcategorias

---

### 4️⃣ DASHBOARD EXECUTIVO

Acesse **"📊 Dashboard Executivo"** para visualizar:

#### 📊 Indicadores Principais
- Mercado 6M
- Ticket mercado vs ticket cliente
- Share atual estimado
- Margem de lucro

#### 🎯 Score e Status
- Gauge visual com score (0-1)
- Classificação: **FOCO** (verde), **OK** (amarelo), **EVITAR** (vermelho)
- Comparação de tickets (dentro/fora do range)

#### 💰 Simulação de Cenários

**3 cenários automáticos:**

1. **Conservador (0,2% share)**
   - Meta realista com baixo investimento

2. **Provável (0,5% share)**
   - Meta esperada com investimento moderado

3. **Otimista (1,0% share)**
   - Meta agressiva com investimento alto

**Para cada cenário, veja:**
- ✅ Receita projetada (6 meses)
- ✅ Lucro projetado (6 meses)
- ✅ Delta vs situação atual
- ✅ Crescimento percentual

#### 📈 Gráficos Interativos
- Evolução da categoria
- Ranking de subcategorias
- Tamanho de mercado (treemap)
- Comparação de cenários
- Crescimento percentual

---

## 🎯 INTERPRETAÇÃO DOS RESULTADOS

### Status das Subcategorias

| Status | Significado | Ação Recomendada |
|--------|-------------|------------------|
| 🟢 **FOCO** | Melhor oportunidade (score alto + ticket OK) | **PRIORIZAR** - Investir recursos aqui |
| 🟡 **OK** | Oportunidade secundária (score médio) | Considerar após FOCO |
| 🔴 **EVITAR** | Não recomendado (score baixo ou ticket desalinhado) | **NÃO INVESTIR** - Focar em outras |

### Leitura do Fit de Ticket

- ✅ **"Ticket OK"** → Cliente está alinhado com o mercado
- ⬇️ **"Reduzir ticket"** → Cliente precisa baixar preço
- ⬆️ **"Aumentar ticket"** → Cliente pode aumentar preço

---

## 💡 EXEMPLO PRÁTICO

### Caso: Tamoyo (Ferramentas)

**Entrada:**
- Ticket: R$ 204,34 | Margem: 15% | Faturamento 3M: R$ 33.511

**Resultado da Análise:**

| Subcategoria | Mercado 6M | Status | Score |
|--------------|------------|--------|-------|
| **Ferramentas Elétricas** | R$ 3,73 bi | **🟢 FOCO** | 1.00 |
| Ferramentas Manuais | R$ 583 mi | 🔴 EVITAR | 0.23 |
| Acessórios | R$ 555 mi | 🔴 EVITAR | 0.22 |

**Recomendação:** Focar em **Ferramentas Elétricas**

**Cenário Provável (0,5% share):**
- Receita 6M: **R$ 18.650.000**
- Crescimento: **278x** vs atual 🚀
- Lucro: **R$ 27.975**

---

## 🔄 DICAS DE USO

### ✅ Boas Práticas

1. **Dados Confiáveis:** Use dados reais de marketplaces (Mercado Livre, Amazon, etc.)
2. **Múltiplas Subcategorias:** Adicione pelo menos 5-7 para comparação robusta
3. **Histórico:** Se possível, adicione dados de categoria para contexto
4. **Range Adequado:** Ajuste o range de ticket conforme a realidade do mercado

### 🎨 Personalização

- **Ticket Custom:** Teste diferentes preços na simulação
- **Range:** Aumente/diminua tolerância conforme elasticidade do mercado
- **Cenários:** Use os 3 cenários para pitch de investidores

### 📊 Exportação (Futuro)

Em breve:
- Exportar relatório em PDF
- Salvar análises em JSON
- Importar dados de Excel

---

## 🆘 PRECISA DE AJUDA?

### Erros Comuns

**❌ "Preencha dados do cliente primeiro"**
→ Vá em "👤 Dados do Cliente" e complete o formulário

**❌ "Adicione pelo menos 3 subcategorias"**
→ Vá em "🎯 Mercado Subcategorias" e adicione mais subcategorias

**❌ Score todos zerados**
→ Verifique se faturamento e unidades foram preenchidos corretamente

### Contato

- 🐛 **Bugs:** Abra uma issue no GitHub
- 💡 **Sugestões:** Pull requests são bem-vindos!
- 📧 **Suporte:** Deixe comentário no repositório

---

## 🚀 PRÓXIMOS PASSOS

Após usar a ferramenta, você terá:

1. ✅ **Ranking claro** de subcategorias priorizadas
2. ✅ **Validação de ticket** (ajustar ou não preço)
3. ✅ **Projeções financeiras** em 3 cenários
4. ✅ **Apresentação executiva** pronta (use capturas de tela)

**Use para:**
- 🎯 Decidir portfólio estratégico
- 💰 Pitch para investidores
- 📊 Planejamento comercial
- 🤝 Negociação com marketplaces

---

## 📱 LINKS ÚTEIS

- **🌐 Aplicação:** https://8501-iop68hor4a5nswkx5ljlg-8f57ffe2.sandbox.novita.ai
- **💻 GitHub:** https://github.com/vlima-creator/Tamanho-do-Mercado
- **📖 README Completo:** Ver README.md no repositório

---

<div align="center">

**Desenvolvido com ❤️ usando Streamlit**

[⬆ Voltar ao topo](#-guia-rápido-de-uso)

</div>
