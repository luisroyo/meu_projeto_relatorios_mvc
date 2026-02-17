# Configurações do Gunicorn para o projeto de relatórios
import os

# Configurações básicas
bind = f"0.0.0.0:{os.getenv('PORT', 5000)}"
workers = int(os.getenv('WEB_CONCURRENCY', 1))
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 100

# Configurações de segurança
limit_request_line = 8192  # Aumenta de 4094 para 8192
limit_request_fields = 100
limit_request_field_size = 8192

# Configurações de logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Configurações de performance
preload_app = True
worker_tmp_dir = "/dev/shm"  # Usa memória para arquivos temporários

# Configurações específicas para Render
if os.getenv("RENDER"):
    # Configurações otimizadas para Render
    workers = 2
    worker_class = "sync"
    timeout = 120
    keepalive = 5
