# -*- coding: utf-8 -*-
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
import flask

from .blueprints import BLUEPRINTS
from .filters import TEMPLATE_FILTERS
from .globals import TEMPLATE_GLOBALS
from .handlers import ERROR_HANDLERS
from .extensions import EXTENSIONS
from .processors import CONTEXT_PROCESSORS
from .config import get_default_config
from .helpers import JSONEncoder


#: flask app singleton?
class App:

    JINJA_TEMPLATE_GLOBALS = TEMPLATE_GLOBALS
    JINJA_TEMPLATE_FILTERS = TEMPLATE_FILTERS
    JINJA_CONTEXT_PROCESSORS = CONTEXT_PROCESSORS
    FLASK_ERROR_HANDLERS = ERROR_HANDLERS
    FLASK_BLUEPRINTS = BLUEPRINTS
    FLASK_EXTENSIONS = EXTENSIONS

    @classmethod
    def _configure_config(cls, app, develop):
        conf_obj = get_default_config(develop)
        app.config.from_object(conf_obj)

    @classmethod
    def _configure_blueprints(cls, app):
        for blueprint in cls.FLASK_BLUEPRINTS:
            app.register_blueprint(blueprint)

    @classmethod
    def _configure_extensions(cls, app):
        for extension in cls.FLASK_EXTENSIONS:
            extension.init_app(app)

    @classmethod
    def _configure_handlers(cls, app):
        """
        Register error handlers.
        """
        for exc, fn in cls.FLASK_ERROR_HANDLERS:
            app.register_error_handler(exc, fn)

    @classmethod
    def _configure_json_encoding(cls, app):
        app.json_encoder = JSONEncoder

    @classmethod
    def _configure_templating(cls, app):
        tempdir = app.config["PYLOAD_API"].get_cachedir()
        cache_path = os.path.join(tempdir, "jinja")

        os.makedirs(cache_path, exist_ok=True)

        app.create_jinja_environment()

        # NOTE: enable autoescape for all file extensions (included .js)
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

    @classmethod
    def _configure_api(cls, app, pycore):
        app.config["PYLOAD_API"] = pycore.api

    @classmethod
    def _configure_logging(cls, app, pycore):
        # Inject our custom logger
        app.logger = pycore.log.getChild("webui")

    def __new__(cls, pycore, develop=False):
        app = flask.Flask(__name__)

        cls._configure_logging(app, pycore)
        cls._configure_api(app, pycore)
        cls._configure_config(app, develop)
        cls._configure_templating(app)
        cls._configure_json_encoding(app)
        cls._configure_session(app)
        cls._configure_blueprints(app)
        cls._configure_extensions(app)
        cls._configure_handlers(app)

        return app
