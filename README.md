# FinanControl 2.0

Protótipo de controle financeiro pessoal com interface Streamlit, gráficos Plotly e dados fictícios mantidos na sessão do navegador. Não há integração com API ou banco de dados.

## Executar localmente

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

## Estrutura

- `app.py`: navegação, páginas, formulários e gráficos.
- `finance.py`: dados de demonstração, formatação e cálculos financeiros.
- `.streamlit/config.toml`: tema dark roxo.
- `requirements.txt`: dependências do protótipo.

O módulo `finance.py` mantém regras e dados de exemplo separados da interface para facilitar a substituição por um repositório/API REST no futuro.
