# -*- coding: utf-8 -*-
#       ____________
#   ___/       |    \_____________ _                 _ ___
#  /        ___/    |    _ __ _  _| |   ___  __ _ __| |   \
# /    \___/  ______/   | '_ \ || | |__/ _ \/ _` / _` |    \
# \            ◯ |      | .__/\_, |____\___/\__,_\__,_|    /
#  \_______\    /_______|_|   |__/________________________/
#           \  /
#            \/

import os

import flask
import jinja2
from werkzeug.serving import WSGIRequestHandler

from .blueprints import BLUEPRINTS
from .config import get_default_config
from .extensions import EXTENSIONS, THEMES
from .filters import TEMPLATE_FILTERS
from .globals import TEMPLATE_GLOBALS
from .handlers import ERROR_HANDLERS
from .processors import CONTEXT_PROCESSORS


#: flask app singleton?
class App:

    JINJA_TEMPLATE_GLOBALS = TEMPLATE_GLOBALS
    JINJA_TEMPLATE_FILTERS = TEMPLATE_FILTERS
    JINJA_CONTEXT_PROCESSORS = CONTEXT_PROCESSORS
    FLASK_ERROR_HANDLERS = ERROR_HANDLERS
    FLASK_BLUEPRINTS = BLUEPRINTS
    FLASK_EXTENSIONS = EXTENSIONS
    FLASK_THEMES = THEMES


    @classmethod
    def _configure_config(cls, app, develop):
        conf_obj = get_default_config(develop)
        app.config.from_object(conf_obj)

    @classmethod
    def _configure_blueprints(cls, app, path_prefix):
        for blueprint in cls.FLASK_BLUEPRINTS:
            url_prefix = path_prefix if not blueprint.url_prefix else None
            app.register_blueprint(blueprint, url_prefix=url_prefix)

    @classmethod
    def _configure_extensions(cls, app):
        for extension in cls.FLASK_EXTENSIONS:
            extension.init_app(app)

    @classmethod
    def _configure_themes(cls, app, path_prefix=""):
        for theme in cls.FLASK_THEMES:
            theme.init_app(app, path_prefix)

    @classmethod
    def _configure_handlers(cls, app):
        """
        Register app handlers.
        """
        for exc, fn in cls.FLASK_ERROR_HANDLERS:
            app.register_error_handler(exc, fn)

        @app.after_request
        def deny_iframe(response):
            response.headers["X-Frame-Options"] = "DENY"
            return response

    @classmethod
    def _configure_json_encoding(cls, app):
        try:
            from .helpers import JSONProvider
            app.json = JSONProvider(app)

        except ImportError:
            from .helpers import JSONEncoder
            app.json_encoder = JSONEncoder

    @classmethod
    def _configure_templating(cls, app):
        tempdir = app.config["PYLOAD_API"].get_cachedir()
        cache_path = os.path.join(tempdir, "jinja")

        os.makedirs(cache_path, exist_ok=True)

        app.create_jinja_environment()

        # NOTE: enable auto escape for all file extensions (including .js)
        #       maybe this will break .txt rendering, but we don't render this kind of files actually
        #       that does not change 'default_for_string=False' (by default)
        app.jinja_env.autoescape = jinja2.select_autoescape(default=True)
        app.jinja_env.bytecode_cache = jinja2.FileSystemBytecodeCache(cache_path)

        for fn in cls.JINJA_TEMPLATE_FILTERS:
            app.add_template_filter(fn)

        for fn in cls.JINJA_TEMPLATE_GLOBALS:
            app.add_template_global(fn)

        for fn in cls.JINJA_CONTEXT_PROCESSORS:
            app.context_processor(fn)

    @classmethod
    def _configure_session(cls, app):
        tempdir = app.config["PYLOAD_API"].get_cachedir()
        cache_path = os.path.join(tempdir, "flask")
        os.makedirs(cache_path, exist_ok=True)

        app.config["SESSION_FILE_DIR"] = cache_path
        app.config["SESSION_TYPE"] = "filesystem"
        app.config["SESSION_COOKIE_NAME"] = "pyload_session_" + str(app.config["PYLOAD_API"].get_config_value("webui", "port"))
        app.config["SESSION_COOKIE_SAMESITE"] = "Strict"
        app.config["SESSION_COOKIE_SECURE"] = app.config["PYLOAD_API"].get_config_value("webui", "use_ssl")
        app.config["SESSION_PERMANENT"] = False

        session_lifetime = max(app.config["PYLOAD_API"].get_config_value("webui", "session_lifetime"), 1) * 60
        app.config["PERMANENT_SESSION_LIFETIME"] = session_lifetime

    @classmethod
    def _configure_api(cls, app, pycore):
        app.config["PYLOAD_API"] = pycore.api

    @classmethod
    def _configure_logging(cls, app, pycore):
        # Inject our custom logger
        app.logger = pycore.log.getChild("webui")

    def __new__(cls, pycore, develop=False, path_prefix=None):
        app = flask.Flask(__name__)

        cls._configure_logging(app, pycore)
        cls._configure_api(app, pycore)
        cls._configure_config(app, develop)
        cls._configure_templating(app)
        cls._configure_json_encoding(app)
        cls._configure_session(app)
        cls._configure_blueprints(app, path_prefix)
        cls._configure_extensions(app)
        cls._configure_themes(app, path_prefix or "")
        cls._configure_handlers(app)

        WSGIRequestHandler.protocol_version = "HTTP/1.1"

        return app
