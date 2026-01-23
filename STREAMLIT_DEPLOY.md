# Deploy do Dashboard MelieADs no Streamlit Cloud

## 📋 Pré-requisitos

1. **Conta GitHub** - O repositório deve estar público ou você deve ter acesso
2. **Conta Streamlit Cloud** - Criar em https://streamlit.io/cloud
3. **Arquivo requirements.txt** - Já incluído no repositório

## 🚀 Passos para Deploy

### 1. Preparar o Repositório GitHub

```bash
# Certifique-se de que os arquivos estão no GitHub
git add streamlit_dashboard.py requirements.txt .streamlit/config.toml data_loader.py
git commit -m "Adicionar dashboard Streamlit com deploy automático"
git push origin main
```

### 2. Conectar ao Streamlit Cloud

1. Acesse https://share.streamlit.io/
2. Clique em **"New app"**
3. Selecione:
   - **Repository**: `vlima-creator/MelieADs`
   - **Branch**: `main`
   - **Main file path**: `streamlit_dashboard.py`

### 3. Configurar Variáveis de Ambiente (Opcional)

Se precisar de variáveis secretas (API keys, etc.):

1. No Streamlit Cloud, vá para **Settings** → **Secrets**
2. Adicione suas variáveis no formato TOML:

```toml
[database]
host = "seu-host"
user = "seu-usuario"
password = "sua-senha"
```

### 4. Acessar o App

Após o deploy, você receberá um link público como:
```
https://melieads-dashboard.streamlit.app/
```

## 🔄 Deploy Automático

O Streamlit Cloud faz deploy automático sempre que você faz push para o GitHub:

```bash
# Faça mudanças no código
git add .
git commit -m "Atualizar dashboard"
git push origin main

# O app será atualizado automaticamente em ~1-2 minutos
```

## 📊 Estrutura do Projeto

```
MelieADs/
├── streamlit_dashboard.py    # App principal
├── data_loader.py            # Módulo de dados
├── requirements.txt          # Dependências
├── .streamlit/
│   └── config.toml          # Configuração do Streamlit
└── STREAMLIT_DEPLOY.md      # Este arquivo
```

## 🎨 Personalização

### Mudar Cores

Edite `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#556B2F"        # Verde Militar
backgroundColor = "#0a0a0a"    # Preto Profundo
secondaryBackgroundColor = "#141414"
textColor = "#ffffff"
```

### Adicionar Dados Reais

Modifique `data_loader.py` para conectar ao seu banco de dados:

```python
def load_campaign_data():
    # Conectar ao seu banco de dados
    # Retornar DataFrame com dados reais
```

## 🐛 Troubleshooting

### App não está atualizando
- Aguarde 2-3 minutos após o push
- Verifique se o arquivo `streamlit_dashboard.py` está no branch correto

### Erro de dependências
- Atualize `requirements.txt` com as versões corretas
- Faça push das mudanças

### Problema de performance
- Adicione cache com `@st.cache_data`
- Otimize carregamento de dados

## 📞 Suporte

Para mais informações:
- Documentação Streamlit: https://docs.streamlit.io/
- Streamlit Cloud: https://streamlit.io/cloud
- GitHub: https://github.com/vlima-creator/MelieADs

---

**Dashboard MelieADs** © 2026
