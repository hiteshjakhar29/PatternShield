# Gunicorn Configuration for PatternShield
# Production-optimized settings

import os
import multiprocessing

# ============================================================================
# SERVER SOCKET
# ============================================================================

bind = f"0.0.0.0:{os.getenv('PORT', '5000')}"
backlog = 2048

# ============================================================================
# WORKER PROCESSES
# ============================================================================

# Number of worker processes
# Formula: (2 x $num_cores) + 1
workers = int(os.getenv('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))

# Worker class
worker_class = 'sync'  # Can use 'gevent' or 'eventlet' for async

# Threads per worker (for sync workers)
threads = int(os.getenv('GUNICORN_THREADS', 2))

# Worker timeout (seconds)
timeout = 60

# Graceful timeout (seconds)
graceful_timeout = 30

# Keep alive (seconds)
keepalive = 2

# ============================================================================
# WORKER LIFECYCLE
# ============================================================================

# Max requests per worker before restart (prevents memory leaks)
max_requests = 1000
max_requests_jitter = 50

# Worker restart on high memory usage
# max_requests_jitter = 100

# ============================================================================
# LOGGING
# ============================================================================

# Access log
accesslog = '-'  # stdout
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Error log
errorlog = '-'  # stderr
loglevel = os.getenv('LOG_LEVEL', 'info').lower()

# Disable access log for health checks
def skip_health_check(response):
    """Skip logging health check requests"""
    if response.path == '/health':
        return True
    return False

# access_log_filter = skip_health_check  # Uncomment to enable

# ============================================================================
# PROCESS NAMING
# ============================================================================

proc_name = 'patternshield'

# ============================================================================
# SERVER MECHANICS
# ============================================================================

# Preload application code before forking workers
preload_app = True

# Daemon mode (run in background)
daemon = False

# PID file
pidfile = None

# User/Group (if running as root - not recommended)
# user = 'appuser'
# group = 'appuser'

# Temporary directory for sockets
tmp_upload_dir = None

# ============================================================================
# SERVER HOOKS
# ============================================================================

def on_starting(server):
    """Called just before the master process is initialized"""
    server.log.info("Starting PatternShield API server")

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP"""
    server.log.info("Reloading PatternShield API server")

def when_ready(server):
    """Called just after the server is started"""
    server.log.info("PatternShield API server is ready. Spawning workers")

def pre_fork(server, worker):
    """Called just before a worker is forked"""
    pass

def post_fork(server, worker):
    """Called just after a worker has been forked"""
    server.log.info(f"Worker spawned (pid: {worker.pid})")

def pre_exec(server):
    """Called just before a new master process is forked"""
    server.log.info("Forked child, re-executing")

def pre_request(worker, req):
    """Called just before a worker processes the request"""
    # Log request details if needed
    pass

def post_request(worker, req, environ, resp):
    """Called after a worker processes the request"""
    # Log response details if needed
    pass

def worker_int(worker):
    """Called just after a worker received the SIGINT signal"""
    worker.log.info(f"Worker received INT or QUIT signal (pid: {worker.pid})")

def worker_abort(worker):
    """Called when a worker received the SIGABRT signal"""
    worker.log.info(f"Worker received SIGABRT signal (pid: {worker.pid})")

def worker_exit(server, worker):
    """Called just after a worker has been exited"""
    server.log.info(f"Worker exited (pid: {worker.pid})")

# ============================================================================
# SSL (if using SSL termination at application level)
# ============================================================================

# keyfile = '/path/to/keyfile'
# certfile = '/path/to/certfile'
# ca_certs = '/path/to/ca_certs'
# cert_reqs = 0  # ssl.CERT_NONE
# ssl_version = 2  # ssl.PROTOCOL_TLSv1

# ============================================================================
# SECURITY
# ============================================================================

# Limit request line size
limit_request_line = 4096

# Limit number of headers
limit_request_fields = 100

# Limit header size
limit_request_field_size = 8190

# ============================================================================
# PERFORMANCE TUNING
# ============================================================================

# Recycle workers after serving N requests (prevents memory leaks)
max_requests = 1000
max_requests_jitter = 100

# Worker temporary file directory
worker_tmp_dir = '/dev/shm'  # Use RAM for temporary files (Linux only)

# ============================================================================
# DEBUGGING (disable in production)
# ============================================================================

# Reload on code changes (development only)
reload = False

# Reload on template changes
reload_extra_files = []

# Check config file for changes
reload_engine = 'auto'
