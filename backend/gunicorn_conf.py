"""Gunicorn configuration for production deployment."""
import multiprocessing
import os

# Workers
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"

# Socket binding
bind = "unix:/tmp/avaliador-api.sock"  # Using socket instead of port for nginx

# Logging
loglevel = "info"
# Ensure log directory exists
log_dir = "/var/log/avaliador-api"
os.makedirs(log_dir, exist_ok=True)
accesslog = f"{log_dir}/access.log"
errorlog = f"{log_dir}/error.log"

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

# SSL/TLS settings 
# Will be handled by Nginx, but we'll ensure the Gunicorn app only accepts local connections
forwarded_allow_ips = "127.0.0.1"

# Security settings
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Proxy header settings (for security)
secure_scheme_headers = {
    'X-FORWARDED-PROTO': 'https',
}

# Daemonize (no need when using systemd)
daemon = False
