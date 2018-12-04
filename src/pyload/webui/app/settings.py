# -*- coding: utf-8 -*-

import os
from pyload import PKGDIR

from pyload.core.utils import random_string


class Config(object):
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SAMESITE = "Lax"
    #: Extensions
    BCRYPT_LOG_ROUNDS = 13
    DEBUG_TB_ENABLED = False
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    CACHE_TYPE = "null"
    THEME_PATHS = os.path.join(PKGDIR, "webui", "app", "themes")


class ProductionConfig(Config):
    ENV = "production"
    SECRET_KEY = "dev"  # TODO: change
    #: Extensions
    CACHE_TYPE = "simple"


class DevelopmentConfig(Config):
    ENV = "development"
    DEBUG = True
    SECRET_KEY = random_string(16)
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


def get_config(debug=False):
    return DevelopmentConfig if debug else ProductionConfig
