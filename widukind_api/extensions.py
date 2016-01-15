# -*- coding: utf-8 -*-

from flask_cache import Cache
from flask_basicauth import BasicAuth
from flask_mail import Mail

cache = Cache()

auth = BasicAuth()

mail = Mail()

