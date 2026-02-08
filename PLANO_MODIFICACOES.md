# Plano de Modificações de Layout

## Objetivo
Adaptar o layout da aplicação Streamlit para seguir o padrão visual da imagem de referência, mantendo toda a funcionalidade existente.

## Estratégia de Implementação

### 1. CSS Customizado Extensivo
Criar um arquivo CSS embutido no `app.py` que sobrescreva os estilos padrão do Streamlit para alcançar o visual desejado.

### 2. Modificações no app.py

#### A. Paleta de Cores
- Background principal: `#000000` (preto puro)
- Cards: `#1a1a1a` com bordas sutis
- Texto principal: `#FFFFFF`
- Texto secundário: `#A0A0A0`
- Acento/Destaque: `#00FF00` (verde)

#### B. Estrutura de Cards de Métricas
Criar função para gerar cards HTML customizados com:
- Ícone circular no topo
- Label em maiúsculas
- Valor destacado
- Bordas arredondadas

#### C. Navegação
Substituir `st.radio()` por `st.tabs()` para navegação horizontal no estilo da referência.

#### D. Sidebar Customizada
Adicionar HTML/CSS para customizar a sidebar com:
- Logo/título estilizado
- Seção de upload com visual aprimorado
- Filtros com badges coloridos

#### E. Header Principal
Criar header customizado com:
- Título grande em maiúsculas
- Subtítulo descritivo
- Ícone de gráfico
- Card com borda arredondada

### 3. Ícones
Utilizar Unicode ou Font Awesome (via CDN) para adicionar ícones aos cards:
- 📦 Total de Anúncios
- 💰 Faturamento Total
- 📊 Quantidade Total
- 🎯 Ticket Médio

### 4. Tipografia
- Títulos: `font-weight: bold`, `text-transform: uppercase`
- Labels: `font-size: 0.85rem`, `text-transform: uppercase`
- Valores: `font-size: 1.8rem`, `font-weight: bold`

### 5. Grid Layout
Utilizar `st.columns()` com proporções adequadas para criar grid de 4 colunas para os cards de métricas.

## Arquivos a Modificar

1. **app.py** - Arquivo principal
   - Adicionar CSS customizado extensivo
   - Criar funções para gerar cards HTML
   - Modificar estrutura de navegação
   - Adicionar header customizado
   - Ajustar sidebar

2. **Nenhum arquivo de funcionalidade será modificado**
   - `utils/market_analyzer.py` - Mantido intacto
   - `utils/visualizations.py` - Mantido intacto
   - `utils/pdf_generator.py` - Mantido intacto

## Compatibilidade
Todas as modificações serão puramente visuais (HTML/CSS), garantindo que:
- Toda a lógica de negócio permaneça inalterada
- Funcionalidades existentes continuem operando normalmente
- Dados e cálculos não sejam afetados
- Importação de Excel continue funcionando
- Geração de PDF continue funcionando

## Testes Necessários
1. Verificar que todos os menus/seções continuam acessíveis
2. Confirmar que os formulários funcionam corretamente
3. Validar que os gráficos são exibidos adequadamente
4. Testar importação de Excel
5. Testar geração de relatório PDF
6. Verificar responsividade em diferentes tamanhos de tela
