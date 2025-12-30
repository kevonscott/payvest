# Gunicorn configuration for payvest production deployment

bind = "0.0.0.0:8000"
workers = 4
worker_class = "gthread"
timeout = 120
loglevel = "info"
accesslog = "-"
errorlog = "-"
preload_app = True
capture_output = True
enable_stdio_inheritance = True
factory = True

# Entry point: Flask factory
wsgi_app = "app:create_app()"
