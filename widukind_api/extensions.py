# -*- coding: utf-8 -*-

from flask_cache import Cache
from flask_basicauth import BasicAuth
from flask_mail import Mail
from flask_limiter import Limiter

cache = Cache()

auth = BasicAuth()

mail = Mail()

limiter = Limiter()
