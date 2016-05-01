# -*- coding: utf-8 -*-

try:
    import multiprocessing
    CPU_COUNT = (multiprocessing.cpu_count() * 2) +1
except:
    CPU_COUNT = 1

from decouple import config as env_config

bind = '0.0.0.0:8080'

daemon = False

chdir = "/code"

preload = env_config('WIDUKIND_API_PRELOAD', False, cast=bool)

proxy_protocol = env_config('WIDUKIND_API_PROXY_PROTOCOL', True, cast=bool)

proxy_allow_ips = env_config('WIDUKIND_API_PROXY_ALLOW_IPS', "127.0.0.1")

forwarded_allow_ips = env_config('WIDUKIND_API_FORWARDED_ALLOW_IPS', "*")

workers = env_config('WIDUKIND_API_WORKERS', CPU_COUNT, cast=int)

worker_class = env_config('WIDUKIND_API_WORKER_CLASS', 'gevent_wsgi')

worker_connections = env_config('WIDUKIND_API_WORKER_CONNECTIONS', 200, cast=int)

backlog = env_config('WIDUKIND_API_BACKLOG', 2048, cast=int)

timeout = env_config('WIDUKIND_API_TIMEOUT', 360, cast=int)

keepalive = env_config('WIDUKIND_API_KEEPALIVE', 2, cast=int)

debug = env_config('WIDUKIND_API_DEBUG', False, cast=bool)

#TODO: logger_class
loglevel = env_config('WIDUKIND_API_LOG_LEVEL', 'info')

accesslog = env_config('WIDUKIND_API_ACCESSLOG', "-")

errorlog = env_config('WIDUKIND_API_ERRORLOG', "-")

syslog = env_config('WIDUKIND_API_SYSLOG', False, cast=bool)

#TODO: limit_request_line=4094
#TODO: limit_request_fields=100
#TODO: limit_request_field_size=8190
#TODO: tmp_upload_dir

if syslog:
    #use --link=syslog:syslog
    #tcp://HOST:PORT
    syslog_addr = env_config('WIDUKIND_API_SYSLOG_ADDR', 'udp://syslog:514')


logconfig = env_config('WIDUKIND_API_LOGCONFIG', None)

statsd_enable = env_config('WIDUKIND_API_STATSD_ENABLE', False, cast=bool)

if statsd_enable:
    #host:port
    statsd_host = env_config('WIDUKIND_API_STATSD_HOST', None)
    statsd_prefix = env_config('WIDUKIND_API_STATSD_PREFIX', 'widukind.browser')
