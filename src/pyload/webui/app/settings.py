# -*- coding: utf-8 -*-

import os
from pyload import PKGDIR

from pyload.core.utils import random_string


class BaseConfig(object):
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SAMESITE = "Lax"
    #: Extensions
    BCRYPT_LOG_ROUNDS = 13
    DEBUG_TB_ENABLED = False
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    CACHE_TYPE = "null"
    THEME_PATHS = os.path.join(PKGDIR, "webui", "app", "themes")


class ProductionConfig(BaseConfig):
    ENV = "production"
    SECRET_KEY = random_string(16)
    #: Extensions
    CACHE_TYPE = "simple"


class DevelopmentConfig(BaseConfig):
    ENV = "development"
    DEBUG = True
    SECRET_KEY = "dev"
    TEMPLATES_AUTO_RELOAD = True
    EXPLAIN_TEMPLATE_LOADING = True
    #: Extensions
    DEBUG_TB_ENABLED = True
    CACHE_NO_NULL_WARNING = True
    LOGIN_DISABLED = True
    SESSION_PROTECTION = None


class TestingConfig(DevelopmentConfig):
    TESTING = True
    #: Extensions
    BCRYPT_LOG_ROUNDS = 4
    