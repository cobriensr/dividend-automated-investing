# pylint: disable=missing-module-docstring, invalid-name, missing-final-newline
# Gunicorn configuration file
import multiprocessing

# WSGI Application
wsgi_app = "wsgi:app"

# Socket Path
bind = '0.0.0.0:5001'

# Worker Options
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'gevent'

# Logging Options
loglevel = 'debug'
errorlog = '-'  # Log to stderr
accesslog = '-'  # Log to stdout
