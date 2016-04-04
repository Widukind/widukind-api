# -*- coding: utf-8 -*-

import os

from decouple import config
gettext = lambda s: s

class Config(object):
    
    WIDUKIND_WEB_URL = config('WIDUKIND_WEB_URL', "http://widukind.cepremap.org")
    
    NO_LIMITED_IPS = []
    NO_LIMITED_COUNTRIES = []
    
    GOOGLE_ANALYTICS_ID = config('WIDUKIND_API_GOOGLE_ANALYTICS_ID', None)
    
    CACHE_TYPE = config('WIDUKIND_CACHE_TYPE', "simple")
    CACHE_KEY_PREFIX = "widukind_api"
    
    ENABLE_CACHE = config('WIDUKIND_API_ENABLE_CACHE', True, cast=bool)
    
    ENABLE_REDIS = config('WIDUKIND_API_ENABLE_REDIS', False, cast=bool)
    
    CACHE_REDIS_URL = config('WIDUKIND_REDIS_URL', 'redis://localhost:6379/0')
    
    if ENABLE_CACHE and ENABLE_REDIS:
        CACHE_TYPE = "redis"
        CACHE_REDIS_URL = config('WIDUKIND_REDIS_URL', 'redis://localhost:6379/0')
        RATELIMIT_STORAGE_URL = config('WIDUKIND_REDIS_URL', 'redis://localhost:6379/0')
    else:
        RATELIMIT_ENABLED = False
        
    RATELIMIT_HEADERS_ENABLED = True
    
    MONGODB_URL = config('WIDUKIND_MONGODB_URL', 'mongodb://localhost/widukind')
    
    SECRET_KEY = config('WIDUKIND_API_SECRET_KEY', 'very very secret key key key')
    
    DEBUG = config('WIDUKIND_API_DEBUG', False, cast=bool)
        
    SENTRY_DSN = config('WIDUKIND_API_SENTRY_DSN', None)
    
    SESSION_ENGINE_ENABLE = config('WIDUKIND_API_SESSION_ENGINE_ENABLE', True, cast=bool)

    #---Flask-Compress
    COMPRESS_LEVEL = 6
    COMPRESS_MIN_SIZE = 500
    COMPRESS_MIMETYPES = ['text/html', 'text/css', 'text/xml',
                          'application/json', 'application/xml']

    #---Flask-Babel
    TIMEZONE = "UTC"#"Europe/Paris" 
    
    #---Flask-Basic-Auth
    BASIC_AUTH_USERNAME = config('WIDUKIND_API_USERNAME', 'admin')
    BASIC_AUTH_PASSWORD = config('WIDUKIND_API_PASSWORD', 'admin')
    BASIC_AUTH_REALM = ''

    #---Mongo Logging Handler    
    LOGGING_MONGO_ENABLE = config('WIDUKIND_API_LOGGING_MONGO_ENABLE', True, cast=bool)
    LOGGING_MAIL_ENABLE = config('WIDUKIND_API_LOGGING_MAIL_ENABLE', False, cast=bool)

    MAIL_ADMINS = config('WIDUKIND_API_MAIL_ADMIN', "root@localhost.com")
    
    #---Flask-Mail
    MAIL_SERVER = config('WIDUKIND_API_MAIL_SERVER', "127.0.0.1")
    MAIL_PORT = config('WIDUKIND_API_MAIL_PORT', 25, cast=int)
    MAIL_USE_TLS = config('WIDUKIND_API_MAIL_USE_TLS', False, cast=bool)
    MAIL_USE_SSL = config('WIDUKIND_API_MAIL_USE_SSL', False, cast=bool)
    #MAIL_DEBUG : default app.debug
    MAIL_USERNAME = None
    MAIL_PASSWORD = None
    MAIL_DEFAULT_SENDER = config('WIDUKIND_API_MAIL_DEFAULT_SENDER', "root@localhost.com")
    MAIL_MAX_EMAILS = None
    #MAIL_SUPPRESS_SEND : default app.testing
    MAIL_ASCII_ATTACHMENTS = False
    
        
class Prod(Config):
    pass

class Dev(Config):
    
    MONGODB_URL = config('WIDUKIND_MONGODB_URL', 'mongodb://localhost/widukind_dev')

    DEBUG = True

    SECRET_KEY = 'dev_key'
    
    MAIL_DEBUG = True
    
class Test(Config):

    MONGODB_URL = config('WIDUKIND_MONGODB_URL', 'mongodb://localhost/widukind_test')
    
    COUNTERS_ENABLE = False

    TESTING = True    
    
    SECRET_KEY = 'test_key'
    
    WTF_CSRF_ENABLED = False
    
    PROPAGATE_EXCEPTIONS = True
    
    CACHE_TYPE = "null"
    
    MAIL_SUPPRESS_SEND = True
    
    ENABLE_REDIS = False
    
    RATELIMIT_ENABLED = False
    

class Custom(Config):
    pass

