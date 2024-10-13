# pylint: disable=missing-module-docstring, invalid-name, missing-final-newline

# Gunicorn configuration file
import multiprocessing

# Socket Path
bind = '0.0.0.0:5000'

# Worker Options
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'gevent'

# Logging Options
loglevel = 'debug'
accesslog = '/path/to/access.log'
errorlog = '/path/to/error.log'