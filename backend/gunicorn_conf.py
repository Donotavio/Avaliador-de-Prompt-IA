"""Gunicorn configuration for production deployment."""
import multiprocessing

# Workers
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"

# Socket binding
bind = "unix:/tmp/gunicorn.sock"  # Using socket instead of port for nginx

# Logging
loglevel = "info"
accesslog = "/var/log/gunicorn/access.log"
errorlog = "/var/log/gunicorn/error.log"

# Process naming
proc_name = "avaliador_prompt_api"

# Timeout config
timeout = 120  # Seconds
graceful_timeout = 30

# Misc configurations
keepalive = 5
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
