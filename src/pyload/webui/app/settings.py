# -*- coding: utf-8 -*-

import os

from builtins import PKGDIR
from pyload.utils.utils import random_string


class Config(object):
    PROJECT = "app"
    APP_DIR = os.path.abspath(os.path.join(PKGDIR, "webui", "app"))
    # PROJECT_ROOT = os.path.abspath(os.path.join(APP_DIR, os.pardir))
    PROJECT_ROOT = APP_DIR
    DEBUG = False
    TESTING = False
    #: extensions
    BCRYPT_LOG_ROUNDS = 13
    DEBUG_TB_ENABLED = False
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    CACHE_TYPE = 'null'

class ProductionConfig(Config):
    ENV = 'production'
    SECRET_KEY = 'dev'  # TODO: change
    #: extensions
    CACHE_TYPE = 'simple'

class DevelopmentConfig(Config):
    ENV = 'development'
    DEBUG = True
    SECRET_KEY = random_string(16)
    TEMPLATES_AUTO_RELOAD = True
    EXPLAIN_TEMPLATE_LOADING = True
    #: extensions
    DEBUG_TB_ENABLED = True

class TestingConfig(DevelopmentConfig):
    TESTING = True
    #: extensions
    BCRYPT_LOG_ROUNDS = 4

    
def get_config(debug=False):  
    return DevelopmentConfig if debug else ProductionConfig
    