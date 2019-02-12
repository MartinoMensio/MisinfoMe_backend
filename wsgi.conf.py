import multiprocessing

bind = '0.0.0.0:5000'
timeout = 60
#worker_class = 'gevent'
# http://docs.gunicorn.org/en/stable/design.html#how-many-workers
workers = multiprocessing.cpu_count() * 2 + 1
#threads = 64