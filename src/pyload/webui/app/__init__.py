# -*- coding: utf-8 -*-
# AUTHOR: vuolter
#      ____________
#   _ /       |    \ ___________ _ _______________ _ ___ _______________
#  /  |    ___/    |   _ __ _  _| |   ___  __ _ __| |   \\    ___  ___ _\
# /   \___/  ______/  | '_ \ || | |__/ _ \/ _` / _` |    \\  / _ \/ _ `/ \
# \       |   o|      | .__/\_, |____\___/\__,_\__,_|    // /_//_/\_, /  /
#  \______\    /______|_|___|__/________________________//______ /___/__/
#          \  /
#           \/

import os

import jinja2

# from flask_talisman import Talisman
from werkzeug.exceptions import HTTPException
from flask_babel import Babel

# from flask_compress import Compress
# from flask_bcrypt import Bcrypt
# from flask_caching import Cache
from flask_debugtoolbar import DebugToolbarExtension

# from flask_static_compress import FlaskStaticCompress
# from flask_minify import minify
from flask_themes2 import Themes

from pyload.core.network.http.http_request import (
    BAD_STATUS_CODES as BAD_HTTP_STATUS_CODES,
)
from pyload.core.utils import formatSize

from .blueprints import api_blueprint, app_blueprint, cnl_blueprint, json_blueprint
from .filters import date, path_make_absolute, path_make_relative, quotepath, truncate
from .helpers import render_error
from .settings import ProductionConfig, DevelopmentConfig

from flask import Flask
from flask.helpers import locked_cached_property


#: flask app singleton
class App(object):

    JINJA_TMPDIR_NAME = "jinja"
    JINJA_FILTERS = {
        "quotepath": quotepath,
        "truncate": truncate,
        "date": date,
        "path_make_relative": path_make_relative,
        "path_make_absolute": path_make_absolute,
        "formatsize": formatSize,
        "getitem": lambda x, y: x.__getitem__(y),
    }

    FLASK_BLUEPRINTS = [
        api_blueprint.bp,
        cnl_blueprint.bp,
        json_blueprint.bp,
        app_blueprint.bp,
    ]

    @classmethod
    def _new_config(cls, app, develop):
        config = DevelopmentConfig if develop else ProductionConfig
        app.config.from_object(config)

    @classmethod
    def _new_hook(cls, app):
        # log every incoming requests
        @app.before_request
        def before_request():
            app.logger.debug("Requesting {}".format(flask.request.url))

    @classmethod
    def _new_blueprints(cls, app):
        for blueprint in cls.FLASK_BLUEPRINTS:
            app.register_blueprint(blueprint)

    @classmethod
    def _new_extensions(cls, app):
        Babel(app)
        # Bcrypt(app)
        # Cache(app)
        # Compress(app)
        DebugToolbarExtension(app)
        # FlaskStaticCompress(app)
        # login_manager = LoginManager(app)
        # login_manager.login_view = "app.login"
        # minify(app)
        # Talisman(app)
        Themes(app, app_identifier="pyload")

        # @login_manager.user_loader
        # def load_user(userid):
        # return User(userid)

        # @login_manager.unauthorized_handler
        # def unauthorized():
        # messages = ["You dont have permission to access this page."]
        # return render_base(messages)

    @classmethod
    def _new_error_handler(cls, app):
        """
        Register error handlers.
        """

        def handle_error(error):
            """
            Render error template.
            """
            assert isinstance(error, HTTPException)

            messages = [error.description]
            try:
                messages.insert(error.response.status)
            except AttributeError:
                pass

            return render_error(messages), error.code

        for code in BAD_HTTP_STATUS_CODES:
            app.register_error_handler(code, handle_error)

    @classmethod
    def _new_jinja_env(cls, app):
        cachedir = app.config["PYLOAD_API"].get_cachedir()
        cache_path = os.path.join(cachedir, cls.JINJA_TMPDIR_NAME)

        os.makedirs(cache_path, exist_ok=True)

        app.create_jinja_environment()
        app.jinja_env.bytecode_cache = jinja2.FileSystemBytecodeCache(cache_path)
        app.jinja_env.filters.update(cls.JINJA_FILTERS)

    @classmethod
    def _new_api(cls, app, pycore):
        app.config["PYLOAD_API"] = pycore.api

    def __new__(cls, pycore, develop=False):

        # Use custom logger name
        # NOTE: flask.app logger is still logging somewhere...
        class _Flask(Flask):
            @locked_cached_property
            def logger(self):
                return pycore.log.getChild("webui")

        app = _Flask(__name__)

        cls._new_api(app, pycore)
        cls._new_config(app, develop)
        # cls._new_hook(app)
        cls._new_blueprints(app)
        cls._new_extensions(app)
        cls._new_error_handler(app)
        cls._new_jinja_env(app)

        return app
