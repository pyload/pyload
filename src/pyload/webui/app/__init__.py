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
import flask
from flask.helpers import locked_cached_property

from .blueprints import BLUEPRINTS
from .filters import FILTERS
from .extensions import EXTENSIONS
from .helpers import render_error
from .config import get_default_config


#: flask app singleton
class App(object):

    JINJA_FILTERS = FILTERS
    FLASK_BLUEPRINTS = BLUEPRINTS
    FLASK_EXTENSIONS = EXTENSIONS

    @classmethod
    def _new_config(cls, app, develop):
        conf_obj = get_default_config(develop)
        app.config.from_object(conf_obj)

    @classmethod
    def _new_blueprints(cls, app):
        for blueprint in cls.FLASK_BLUEPRINTS:
            app.register_blueprint(blueprint)

    @classmethod
    def _new_extensions(cls, app):
        for extension in cls.FLASK_EXTENSIONS:
            extension.init_app(app)
        # FlaskStaticCompress(app)
        # login_manager = LoginManager(app)
        # login_manager.login_view = "app.login"

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
        def handle_error(exc):
            code = 500
            try:
                code = exc.code
            except AttributeError:
                pass
            messages = ["Sorry, something went wrong... :(", str(exc)]
            return render_error(messages), code
            
        app.register_error_handler(Exception, handle_error)
            

    @classmethod
    def _new_jinja_env(cls, app):
        cachedir = app.config["PYLOAD_API"].get_cachedir()
        cache_path = os.path.join(cachedir, "jinja")

        os.makedirs(cache_path, exist_ok=True)

        app.create_jinja_environment()
        app.jinja_env.bytecode_cache = jinja2.FileSystemBytecodeCache(cache_path)
        app.jinja_env.filters.update(cls.JINJA_FILTERS)

    @classmethod
    def _new_session(cls, app):
        cachedir = app.config["PYLOAD_API"].get_cachedir()
        cache_path = os.path.join(cachedir, "flask")
        
        os.makedirs(cache_path, exist_ok=True)
        
        app.config["SESSION_FILE_DIR"] = cache_path
    
    @classmethod
    def _new_api(cls, app, pycore):
        app.config["PYLOAD_API"] = pycore.api

    def __new__(cls, pycore, develop=False):
        # Use custom logger name
        class Flask(flask.Flask):
            @locked_cached_property
            def logger(self):
                return pycore.log.getChild("webui")

        app = Flask(__name__)

        cls._new_api(app, pycore)
        cls._new_config(app, develop)
        cls._new_jinja_env(app)
        cls._new_session(app)
        cls._new_blueprints(app)
        cls._new_extensions(app)
        cls._new_error_handler(app)

        return app
