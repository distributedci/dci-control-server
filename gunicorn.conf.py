import logging
import os

logger = logging.getLogger(__name__)

# Don't manage workers with gunicorn but by spawning more containers and let haproxy handle balancing
DEFAULT_NB_WORKERS = 1
workers = int(os.getenv("DCI_NB_WORKERS", DEFAULT_NB_WORKERS))
worker_connections = int(os.getenv("DCI_GUNICORN_WORKER_CONNECTIONS", 50))
worker_class = "gevent"

# Restart worker after a certain amount of requests to mitigate memory leaks, etc. …
if os.getenv("DCI_GUNICORN_MAX_REQUESTS") is not None:
    max_requests = int(os.getenv("DCI_GUNICORN_MAX_REQUESTS"))
# Add some jitter to avoid all workers restarting at the same time.
if os.getenv("DCI_GUNICORN_MAX_REQUESTS_JITTER") is not None:
    max_requests_jitter = int(os.getenv("DCI_GUNICORN_MAX_REQUESTS_JITTER"))

if os.getenv("DCI_GUNICORN_TIMEOUT") is not None:
    timeout = int(os.getenv("DCI_GUNICORN_TIMEOUT"))

if os.getenv("DCI_GUNICORN_GRACEFUL_TIMEOUT") is not None:
    graceful_timeout = int(os.getenv("DCI_GUNICORN_GRACEFUL_TIMEOUT"))

accesslog = "-"
access_log_format = (
    '%(h)s:%({x-forwarded-for}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
)


def worker_exit(server, worker):
    app = worker.app.wsgi()
    app.logger.info(
        "Worker exiting pid=%s (master pid=%s)",
        worker.pid,
        server.pid,
    )
    app.stop_publisher()


def post_worker_init(worker):
    app = worker.app.wsgi()
    app.start_publisher()


def worker_int(worker):
    """
    Called by the signal handler for SIGINT and SIGQUIT.
    This runs before the worker exits, wait for last
    in-flight messages to be processed.
    """
    logger.info(
        "Worker %s received shutdown signal, sending STOP sentinel and wait for the queue to be processed...",
        worker.pid,
    )
    app = worker.app.wsgi()
    app.stop_publisher()
    logger.info("Worker %s gracefully complete", worker.pid)
