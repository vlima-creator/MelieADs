# Análise do Layout de Referência

## Características Visuais Identificadas

### 1. **Paleta de Cores**
- **Background principal:** Preto (#000000 ou muito próximo)
- **Cards/Containers:** Cinza escuro (#1a1a1a, #262626)
- **Bordas dos cards:** Bordas sutis com leve brilho
- **Texto principal:** Branco (#FFFFFF)
- **Texto secundário:** Cinza claro (#A0A0A0, #B0B0B0)
- **Destaque/Acento:** Verde (#00FF00 ou similar) para elementos ativos
- **Ícones:** Brancos com fundo circular

### 2. **Estrutura do Layout**

#### **Sidebar (Esquerda)**
- Fundo: Preto/Cinza muito escuro (#0a0a0a)
- Largura: ~240px
- Elementos:
  - Logo/Título no topo: "Curva ABC" com ícone de gráfico
  - Subtítulo: "Diagnóstico & Ações"
  - Seção "Upload de Dados" com ícone de cubo
  - Área de drag-and-drop para arquivos
  - Botão "Browse files"
  - Lista de arquivos carregados
  - Seção "Filtros Globais" com ícone de alvo
  - Filtros de curvas (A, B, C com badges coloridos)

#### **Header Principal**
- Título grande: "CURVA ABC, DIAGNÓSTICO E AÇÕES"
- Subtítulo: "Análise inteligente para decisões rápidas por frente e prioridade"
- Fundo: Card com borda arredondada
- Ícone de gráfico à esquerda do título

#### **Cards de Métricas (KPIs)**
- Layout: Grid de 4 colunas
- Estilo: Cards escuros com bordas arredondadas
- Estrutura de cada card:
  - Ícone circular no topo (branco com fundo transparente)
  - Label em maiúsculas (cinza claro)
  - Valor grande e destacado (branco)
- Métricas mostradas:
  1. TOTAL DE ANÚNCIOS: 202
  2. FATURAMENTO TOTAL: R$ 871.096,11
  3. QUANTIDADE TOTAL: 3.544
  4. TICKET MÉDIO: R$ 245,79

#### **Navegação por Tabs**
- Tabs horizontais: DASHBOARD, LISTAS E EXPORTAÇÃO, PLANO TÁTICO, RELATÓRIO ESTRATÉGICO
- Tab ativa: Borda inferior verde
- Texto: Maiúsculas, cinza claro

#### **Seção de Filtros**
- Título: "Selecione o Período para Análise"
- Dropdown: Fundo escuro com texto branco
- Valor selecionado: "0-30"

#### **Cards de Métricas Filtradas**
- Mesmo estilo dos cards superiores
- Grid de 4 colunas
- Métricas específicas do período selecionado:
  1. FATURAMENTO 0-30: R$ 302.319,34
  2. QUANTIDADE 0-30: 1.184
  3. TICKET MÉDIO 0-30: R$ 255,34
  4. CURVA A (0-30): 26

### 3. **Tipografia**
- Títulos principais: Sans-serif, bold, maiúsculas
- Labels: Sans-serif, regular, maiúsculas, menor
- Valores: Sans-serif, bold, grande
- Hierarquia clara entre títulos, labels e valores

### 4. **Espaçamento e Layout**
- Margens consistentes entre elementos
- Padding generoso nos cards
- Border-radius suave (~8-12px)
- Grid responsivo com gaps uniformes

### 5. **Ícones**
- Estilo: Line icons (outline)
- Cor: Branco
- Posicionamento: Centralizados nos cards
- Tamanho: ~32-40px

### 6. **Elementos Interativos**
- Botões: Fundo escuro com borda, texto branco
- Hover states: Provavelmente com mudança de cor/borda
- Dropdowns: Fundo escuro, texto branco, ícone de seta

## Diferenças com o Layout Atual (Streamlit)

1. **Cor de fundo:** Atual usa cinza (#1E1E1E), referência usa preto puro
2. **Sidebar:** Atual usa sidebar padrão do Streamlit, referência tem sidebar customizada
3. **Cards:** Atual tem estilo mais simples, referência tem ícones e estrutura mais elaborada
4. **Navegação:** Atual usa radio buttons, referência usa tabs horizontais
5. **Tipografia:** Referência usa mais maiúsculas e hierarquia mais marcada
6. **Ícones:** Referência tem ícones circulares em todos os cards de métricas

## Plano de Implementação

Para adaptar o layout atual ao padrão de referência, será necessário:

1. Criar CSS customizado extensivo para sobrescrever estilos do Streamlit
2. Adicionar ícones aos cards de métricas
3. Modificar a estrutura de navegação (radio → tabs)
4. Ajustar paleta de cores para tons mais escuros
5. Implementar sidebar customizada com HTML/CSS
6. Adicionar estrutura de grid para os cards de métricas
7. Melhorar tipografia e hierarquia visual
