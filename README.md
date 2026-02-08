# 📊 Análise de Mercado Marketplace

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.31.0-red)
![License](https://img.shields.io/badge/License-MIT-green)

Dashboard interativo para análise estratégica de categorias e subcategorias em marketplaces. Ajuda você a decidir **em qual categoria focar** baseado em dados de mercado e fit de ticket.

## 🎯 Funcionalidades

- ✅ **Análise de Cliente:** Configure dados do seller (ticket, margem, faturamento)
- ✅ **Dados de Mercado:** Adicione evolução temporal da categoria macro
- ✅ **Análise de Subcategorias:** Compare múltiplas oportunidades de mercado
- ✅ **Ranking Automático:** Score e classificação (FOCO/OK/EVITAR)
- ✅ **Simulação de Cenários:** Projeções conservador/provável/otimista
- ✅ **Dashboard Executivo:** Visualizações interativas com Plotly
- ✅ **Cálculos Automáticos:** Score, fit de ticket, share, lucro projetado

## 🚀 Como Usar

### Instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/marketplace-analysis.git
cd marketplace-analysis
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Execute a aplicação:
```bash
streamlit run app.py
```

4. Acesse no navegador: `http://localhost:8501`

## 📖 Passo a Passo

### 1️⃣ Dados do Cliente
Preencha informações básicas:
- Nome da empresa
- Categoria macro
- Ticket médio
- Margem de lucro
- Faturamento médio (últimos 3 meses)
- Unidades vendidas (últimos 3 meses)

### 2️⃣ Mercado Categoria (Opcional)
Adicione dados históricos mensais da categoria para contextualizar tendências.

### 3️⃣ Mercado Subcategorias
Informe pelo menos 3 subcategorias com:
- Faturamento dos últimos 6 meses
- Unidades vendidas dos últimos 6 meses

### 4️⃣ Dashboard Executivo
Visualize:
- Ranking automático de subcategorias
- Score de priorização (0 a 1)
- Status de recomendação (FOCO/OK/EVITAR)
- Simulação de 3 cenários de crescimento
- Gráficos interativos

## 🧠 Metodologia

### Score de Priorização

O score combina dois fatores:

**1. Tamanho de Mercado (70%)**
- Volume de faturamento da subcategoria
- Normalizado de 0 a 1

**2. Fit de Ticket (30%)**
- Alinhamento entre ticket do cliente e ticket do mercado
- Considera range de tolerância configurável (padrão ±20%)

### Status Automático

- 🟢 **FOCO:** Score ≥ 0.7 + Ticket dentro do range → Prioridade máxima
- 🟡 **OK:** Score ≥ 0.4 OU ticket aceitável → Oportunidade secundária
- 🔴 **EVITAR:** Score baixo + ticket desalinhado → Não recomendado

### Cenários

**Conservador (0,2% share):**
- Meta realista com baixo investimento

**Provável (0,5% share):**
- Meta esperada com investimento moderado

**Otimista (1,0% share):**
- Meta agressiva com investimento alto

## 📊 Exemplo Prático

### Caso: Empresa Tamoyo (Ferramentas)

**Dados do Cliente:**
- Ticket médio: R$ 204,34
- Margem: 15%
- Faturamento 3M: R$ 33.511,65

**Análise de Subcategorias:**

| Subcategoria | Mercado 6M | Status | Motivo |
|--------------|------------|--------|--------|
| **Ferramentas Elétricas** | R$ 3,73 bi | **FOCO** ✅ | Mercado gigante + ticket OK |
| Ferramentas Manuais | R$ 583 mi | EVITAR ⚠️ | Ticket muito baixo |
| Acessórios | R$ 555 mi | EVITAR ⚠️ | Ticket muito baixo |

**Cenário Provável (0,5% share em Ferramentas Elétricas):**
- Receita 6M: **R$ 18,65 milhões**
- Crescimento: **278x** vs atual
- Lucro adicional: **R$ 27.975**

## 🛠️ Estrutura do Projeto

```
marketplace-analysis/
├── app.py                          # Aplicação Streamlit principal
├── requirements.txt                # Dependências Python
├── utils/
│   ├── market_analyzer.py         # Lógica de cálculos e análise
│   └── visualizations.py          # Gráficos com Plotly
├── data/                          # Dados salvos (gerado em runtime)
└── README.md                      # Este arquivo
```

## 📦 Dependências

- `streamlit==1.31.0` - Framework web
- `pandas==2.2.0` - Manipulação de dados
- `numpy==1.26.3` - Cálculos numéricos
- `plotly==5.18.0` - Visualizações interativas
- `openpyxl==3.1.2` - Leitura de Excel (futuro)

## 🎨 Recursos Visuais

- **Gráficos Interativos:** Evolução temporal, ranking, comparações
- **Métricas Dinâmicas:** KPIs principais destacados
- **Indicador Gauge:** Score visual com status colorido
- **Tabelas Estilizadas:** Formatação condicional por status
- **Responsivo:** Adapta-se a diferentes tamanhos de tela

## 💡 Casos de Uso

### Para Consultores
- Apresentar análise de mercado para clientes
- Recomendar categorias estratégicas
- Quantificar oportunidades de crescimento

### Para Gestores de Marketplace
- Avaliar novas categorias para expansão
- Priorizar investimentos em portfólio
- Validar fit de ticket de sellers

### Para Sellers
- Decidir em qual categoria entrar
- Ajustar estratégia de precificação
- Projetar receita e lucratividade

## 🔮 Próximas Funcionalidades

- [ ] Exportar relatórios em PDF
- [ ] Salvar/Carregar análises (JSON)
- [ ] Importar dados de Excel
- [ ] Análise de concorrência
- [ ] Sazonalidade mês a mês
- [ ] Integração com APIs de marketplaces
- [ ] Machine Learning para previsões

## 🤝 Contribuindo

Contribuições são bem-vindas! Para contribuir:

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 👨‍💻 Autor

**GenSpark AI Developer**

Baseado no template Excel "Análise de Mercado Marketplace v8"

## 🙏 Agradecimentos

- Baseado no template Excel de análise de mercado
- Desenvolvido com Streamlit
- Visualizações com Plotly

## 📞 Suporte

Para dúvidas ou sugestões, abra uma [issue](https://github.com/seu-usuario/marketplace-analysis/issues) no GitHub.

---

<div align="center">

**Desenvolvido com ❤️ usando Streamlit**

[⬆ Voltar ao topo](#-análise-de-mercado-marketplace)

</div>
