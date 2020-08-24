# -*- coding: utf-8 -*-

from pyload.core.utils.misc import random_string


def get_default_config(develop):
    return DevelopmentConfig if develop else ProductionConfig


class BaseConfig:
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SAMESITE = "Lax"
    #: Extensions
    # BCRYPT_LOG_ROUNDS = 13
    # DEBUG_TB_ENABLED = False
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    CACHE_DEFAULT_TIMEOUT = 300
    # SESSION_TYPE = "filesystem"


class ProductionConfig(BaseConfig):
    ENV = "production"
    SECRET_KEY = random_string(16)
    #: Extensions
    CACHE_TYPE = "simple"
    # SESSION_USE_SIGNER = True


class DevelopmentConfig(BaseConfig):
    ENV = "development"
    DEBUG = True
    SECRET_KEY = "dev"
    TEMPLATES_AUTO_RELOAD = True
    EXPLAIN_TEMPLATE_LOADING = True
    #: Extensions
    # DEBUG_TB_ENABLED = True
    CACHE_NO_NULL_WARNING = True
    # LOGIN_DISABLED = True
    # SESSION_PROTECTION = None


class TestingConfig(DevelopmentConfig):
    TESTING = True
    #: Extensions
    # BCRYPT_LOG_ROUNDS = 4
