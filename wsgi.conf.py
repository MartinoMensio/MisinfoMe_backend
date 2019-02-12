import multiprocessing

bind = '0.0.0.0:5000'
timeout = 60
# using gevent to handle multiple request for each worker using asyncIO
worker_class = 'gevent'
# http://docs.gunicorn.org/en/stable/design.html#how-many-workers
workers = multiprocessing.cpu_count() * 2 + 1
# threads = ? # this is not used by gevent
# worker_connections is default to 1000
worker_connections = 100