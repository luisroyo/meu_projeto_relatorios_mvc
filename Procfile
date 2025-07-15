# Procfile para deploy em produção (Heroku, Render, etc.)
# Ajuste o número de workers conforme a CPU/memória do servidor (recomendado: 2-4 por core)
# Para requisições longas, ajuste o timeout: --timeout 60
web: gunicorn run:app --bind 0.0.0.0:$PORT --workers 4
