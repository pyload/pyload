# -*- coding: utf-8 -*-
# AUTHOR: vuolter

import os
from pyload import PKGDIR
from builtins import str

import flask
import jinja2
from flask.logging import default_handler
# from flask_talisman import Talisman
from flask_babel import Babel
# from flask_compress import Compress
# from flask_bcrypt import Bcrypt
# from flask_caching import Cache
from flask_debugtoolbar import DebugToolbarExtension
# from flask_static_compress import FlaskStaticCompress
# from flask_minify import minify
from flask_themes2 import Themes

from werkzeug.exceptions import HTTPException

from pyload.core.network.http.http_request import (
    BAD_STATUS_CODES as BAD_HTTP_STATUS_CODES)
from pyload.core.utils.utils import formatSize

from .blueprints import api_blueprint, app_blueprint, cnl_blueprint, json_blueprint
from .filters import date, path_make_absolute, path_make_relative, quotepath, truncate
from .helpers import pre_processor, render_template
from .settings import get_config

APP_ROOT_PATH = os.path.join(PKGDIR, "webui", "app")

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

BLUEPRINTS = [api_blueprint.bp, cnl_blueprint.bp, json_blueprint.bp, app_blueprint.bp]


def setup_config(app, config):
    app.config.from_object(config)


def setup_hook(app):
    # log every incoming requests
    @app.before_request
    def before_request():
        app.logger.debug("Requesting {}".format(flask.request.url))


def setup_blueprints(app, blueprints):
    for blueprint in blueprints:
        app.register_blueprint(blueprint)


def setup_logging(app):
    app.logger.removeHandler(default_handler)


def setup_extensions(app):
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
    # return base(messages)


def setup_error_handlers(app):
    """Register error handlers."""

    def render_error(error):
        """Render error template."""
        
        #: https://github.com/pallets/flask/issues/2778
        if not isinstance(error, HTTPException):
            error_code = 500
            error_status = "Server Error"
            error_message = str(error)
        else:
            error_code = error.status_code
            error_status = error.status
            
            if error.is_json:
                error_message = error.get_json().get("error", "Server Error")
            else:
                error_message = str(error.data) or "Server Error"
            
        app.logger.debug("Error {}: {}".format(error_code, error_status), error_message, exc_info=True)
        
        return (
            render_template("error.html", {"messages": [error_status, error_message]}, [pre_processor]),
            error_code,
        )

    for errcode in BAD_HTTP_STATUS_CODES:
        app.register_error_handler(errcode, render_error)


def setup_jinja_env(app):
    cachedir = app.config["PYLOAD_API"].get_cachedir()
    cache_path = os.path.join(cachedir, JINJA_TMPDIR_NAME)

    os.makedirs(cache_path, exist_ok=True)

    app.create_jinja_environment()
    app.jinja_env.bytecode_cache = jinja2.FileSystemBytecodeCache(cache_path)
    app.jinja_env.filters.update(JINJA_FILTERS)


def setup_api(app, api):
    app.config["PYLOAD_API"] = api


def create_app(api, debug=False):
    """Run Flask server"""
    app = flask.Flask(__name__.split(".")[0], root_path=APP_ROOT_PATH)

    setup_api(app, api)
    setup_config(app, get_config(debug))
    # setup_hook(app)
    setup_blueprints(app, BLUEPRINTS)
    setup_extensions(app)
    setup_logging(app)
    setup_error_handlers(app)
    setup_jinja_env(app)

    return app
