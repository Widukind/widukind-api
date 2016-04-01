# -*- coding: utf-8 -*-

import logging

logger = logging.getLogger(__name__)

from werkzeug.contrib.fixers import ProxyFix
from flask import Flask, request, abort, session, g, redirect, url_for, render_template, current_app
from decouple import config as config_from_env

from widukind_api import extensions
from widukind_api import constants
from widukind_api.extensions import cache

def _conf_converters(app):
    
    from werkzeug.routing import BaseConverter, ValidationError
    from bson.objectid import ObjectId
    from bson.errors import InvalidId
    
    class BSONObjectIdConverter(BaseConverter):

        def to_python(self, value):
            try:
                return ObjectId(value)
            except (InvalidId, ValueError, TypeError):
                raise ValidationError()
             
        def to_url(self, value):
            return str(value)    
        
    app.url_map.converters['objectid'] = BSONObjectIdConverter
    

def _conf_logging(debug=False, 
                  stdout_enable=True, 
                  syslog_enable=False,
                  prog_name='widukind_api',
                  config_file=None,
                  LEVEL_DEFAULT="INFO"):

    import sys
    import logging.config
    
    if config_file:
        logging.config.fileConfig(config_file, disable_existing_loggers=True)
        return logging.getLogger(prog_name)
    
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': True,
        'formatters': {
            'debug': {
                'format': 'line:%(lineno)d - %(asctime)s %(name)s: [%(levelname)s] - [%(process)d] - [%(module)s] - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S',
            },
            'simple': {
                'format': '%(asctime)s %(name)s: [%(levelname)s] - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S',
            },
        },    
        'handlers': {
            'null': {
                'level':LEVEL_DEFAULT,
                'class':'logging.NullHandler',
            },
            'console':{
                'level':LEVEL_DEFAULT,
                'class':'logging.StreamHandler',
                'formatter': 'simple'
            },      
        },
        'loggers': {
            '': {
                'handlers': [],
                'level': 'INFO',
                'propagate': False,
            },
            prog_name: {
                #'handlers': [],
                'level': 'INFO',
                'propagate': True,
            },
        },
    }
    
    if sys.platform.startswith("win32"):
        LOGGING['loggers']['']['handlers'] = ['console']

    elif syslog_enable:
        LOGGING['handlers']['syslog'] = {
                'level':'INFO',
                'class':'logging.handlers.SysLogHandler',
                'address' : '/dev/log',
                'facility': 'daemon',
                'formatter': 'simple'    
        }       
        LOGGING['loggers']['']['handlers'].append('syslog')
        
    if stdout_enable:
        if not 'console' in LOGGING['loggers']['']['handlers']:
            LOGGING['loggers']['']['handlers'].append('console')

    '''if handlers is empty'''
    if not LOGGING['loggers']['']['handlers']:
        LOGGING['loggers']['']['handlers'] = ['console']
    
    if debug:
        LOGGING['loggers']['']['level'] = 'DEBUG'
        LOGGING['loggers'][prog_name]['level'] = 'DEBUG'
        for handler in LOGGING['handlers'].keys():
            LOGGING['handlers'][handler]['formatter'] = 'debug'
            LOGGING['handlers'][handler]['level'] = 'DEBUG' 

    #from pprint import pprint as pp 
    #pp(LOGGING)
    #werkzeug = logging.getLogger('werkzeug')
    #werkzeug.handlers = []
             
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(prog_name)
    
    return logger

def _conf_logging_mongo(app):
    #TODO: distinction entre app web et api dans collection
    from widukind_common.mongo_logging_handler import MongoHandler
    handler = MongoHandler(db=app.widukind_db, collection=constants.COL_LOGS)
    handler.setLevel(logging.ERROR)
    app.logger.addHandler(handler)
    
def _conf_logging_mail(app):
    from logging.handlers import SMTPHandler
    
    ADMIN = app.config.get("MAIL_ADMINS", None)
    if not ADMIN:
        app.logger.error("Emails address for admins are not configured")
        return
        
    ADMINS = ADMIN.split(",")
    mail_handler = SMTPHandler(app.config.get("MAIL_SERVER"),
                               app.config.get("MAIL_DEFAULT_SENDER"),
                               ADMINS, 
                               'Application Failed')
    mail_handler.setLevel(logging.ERROR)
    app.logger.addHandler(mail_handler) 
    
def _conf_logging_errors(app):
    
    def log_exception(sender, exception, **extra):
        print("log_exception.exception : ", exception)
        print("log_exception;extra : ", extra)
        sender.logger.error(str(exception))
        
    from flask import got_request_exception
    got_request_exception.connect(log_exception, app)        

def _conf_sentry(app):
    try:
        from raven.contrib.flask import Sentry
        if app.config.get('SENTRY_DSN', None):
            sentry = Sentry(app, logging=True, level=app.logger.level)
    except ImportError:
        pass
    
def _conf_db(app):
    from widukind_common.utils import get_mongo_db
    app.widukind_db = get_mongo_db(app.config.get("MONGODB_URL"))

def _conf_session(app):
    from widukind_common.flask_utils.mongo_session import PyMongoSessionInterface
    app.session_interface = PyMongoSessionInterface(app.widukind_db,
                                                    collection=constants.COL_SESSION)
        
def _conf_cache(app):
    """
    @cache.cached(timeout=50)
    @cache.cached(timeout=50, key_prefix='all_comments')
    @cache.memoize(50)
    """
    cache.init_app(app)

def _conf_limiter(app):
    extensions.limiter.init_app(app)
    
def _conf_compress(app):
    from flask_compress import Compress
    Compress(app)        
    
def _conf_default_views(app):

    @app.route("/", endpoint="home")
    def index():
        return render_template("docs/json.html")
        #return render_template("index.html")

    @app.route("/docs/json", endpoint="docs-json")
    def docs_json():
        return render_template("docs/json.html")

def _conf_auth(app):
    extensions.auth.init_app(app)
    
    @app.context_processor
    def is_auth():
        return dict(is_logged=extensions.auth.authenticate())        
    
def _conf_mail(app):
    extensions.mail.init_app(app)

def _conf_processors(app):
    
    @app.context_processor
    def functions():
        def _split(s):
            return s.split()
        return dict(split=_split)
    
def _conf_bp(app):
    from widukind_api.plugins import html_plugin
    from widukind_api.plugins import eviews_plugin
    from widukind_api.plugins import json_plugin
    from widukind_api.plugins import r_plugin
    from widukind_api.plugins import sdmx_plugin
    #from widukind_api.plugins import rest_json
    #app.register_blueprint(rest_json.bp, url_prefix='/api/v1/json2')    
    
    app.register_blueprint(html_plugin.bp, url_prefix='/api/v1/html')    
    app.register_blueprint(json_plugin.bp, url_prefix='/api/v1/json')    
    app.register_blueprint(eviews_plugin.bp, url_prefix='/api/v1/eviews')
    app.register_blueprint(r_plugin.bp, url_prefix='/api/v1/r')
    app.register_blueprint(sdmx_plugin.bp, url_prefix='/api/v1/sdmx')    
    
def _conf_errors(app):
    
    from werkzeug import exceptions as ex

    class DisabledElement(ex.HTTPException):
        code = 307
        description = 'Disabled element'
    abort.mapping[307] = DisabledElement

    @app.errorhandler(307)
    def disable_error(error):
        values = dict(code=307, error="307 Error", original_error=str(error))
        return app.jsonify(values)
    
    @app.errorhandler(500)
    def error_500(error):
        values = dict(code=500, error="Server Error", original_error=str(error))
        return app.jsonify(values)
    
    @app.errorhandler(404)
    def not_found_error(error):
        values = dict(code=404, error="404 Error", original_error=str(error))
        return app.jsonify(values)

def _conf_jsonify(app):

    from widukind_api import json
    
    def jsonify(obj):
        content = json.dumps(obj)
        return current_app.response_class(content, mimetype='application/json')

    app.jsonify = jsonify
    
def _conf_periods(app):
    
    import pandas
    
    def get_ordinal_from_period(date_str, freq=None):
        if not freq in constants.CACHE_FREQUENCY:
            return pandas.Period(date_str, freq=freq).ordinal
        
        key = "p-to-o-%s.%s" % (date_str, freq)
        value = cache.get(key)
        if value:
            return value
        
        value = pandas.Period(date_str, freq=freq).ordinal
        cache.set(key, value, timeout=300)
        return value
    
    def get_period_from_ordinal(date_ordinal, freq=None):
        if not freq in constants.CACHE_FREQUENCY:
            return str(pandas.Period(ordinal=date_ordinal, freq=freq))
    
        key = "o-to-p-%s.%s" % (date_ordinal, freq)
        value = cache.get(key)
        if value:
            return value
        
        value = str(pandas.Period(ordinal=date_ordinal, freq=freq))
        cache.set(key, value, timeout=300)
        return value
    
    app.get_ordinal_from_period = get_ordinal_from_period
    app.get_period_from_ordinal = get_period_from_ordinal
    
    @app.context_processor
    def convert_pandas_period():
        def convert(date_ordinal, frequency):
            return get_period_from_ordinal(date_ordinal, frequency)
        return dict(pandas_period=convert)

def create_app(config='widukind_api.settings.Prod'):
    
    env_config = config_from_env('WIDUKIND_API_SETTINGS', config)
    
    app = Flask(__name__)
    app.config.from_object(env_config)    

    _conf_db(app)

    app.config['LOGGER_NAME'] = 'widukind_api'
    app._logger = _conf_logging(debug=app.debug, prog_name='widukind_api')
    
    if app.config.get("LOGGING_MONGO_ENABLE", True):
        _conf_logging_mongo(app)

    if app.config.get("LOGGING_MAIL_ENABLE", False):
        _conf_logging_mail(app)

    _conf_logging_errors(app)    
    
    _conf_sentry(app)

    _conf_errors(app)
    
    _conf_cache(app)
    
    _conf_limiter(app)
    
    _conf_compress(app)
    
    _conf_converters(app)
    
    _conf_jsonify(app)

    _conf_default_views(app)
    
    _conf_bp(app)
    
    _conf_processors(app)
    
    _conf_periods(app)
    
    _conf_auth(app)
    
    _conf_session(app)
    
    _conf_mail(app)
    
    app.wsgi_app = ProxyFix(app.wsgi_app)

    return app
