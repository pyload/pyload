# -*- coding: utf-8 -*-
# @author: vuolter

import os
from builtins import str, PKGDIR
import jinja2
from pyload.core.utils.utils import formatSize
import flask

from pyload.core.network.http_request import BAD_STATUS_CODES as BAD_HTTP_STATUS_CODES

# from flask_static_compress import FlaskStaticCompress
from flask_minify import minify
from pyload.webui.app.settings import get_config
from flask_themes2 import Themes

from flask_compress import Compress
# from flask_bcrypt import Bcrypt
# from flask_caching import Cache
from flask_debugtoolbar import DebugToolbarExtension

# from flask_talisman import Talisman
from flask_babel import Babel
from pyload.webui.app.helpers import pre_processor
from pyload.webui.app.blueprints import (
    api_blueprint,
    cnl_blueprint,
    json_blueprint,
    app_blueprint,
)
from pyload.webui.app.filters import (
    date,
    path_make_absolute,
    path_make_relative,
    quotepath,
    truncate,
)
from pyload.webui.app.helpers import render_template
from flask.logging import default_handler


FLASK_ROOT_PATH = os.path.join(PKGDIR, "webui", "app")

JINJA_FILTERS = {
    "quotepath": quotepath,
    "truncate": truncate,
    "date": date,
    "path_make_relative": path_make_relative,
    "path_make_absolute": path_make_absolute,
    "formatsize": formatSize,
    "getitem": lambda x, y: x.__getitem__(y),
}

DEFAULT_BLUEPRINTS = [
    api_blueprint.bp,
    cnl_blueprint.bp,
    json_blueprint.bp,
    app_blueprint.bp,
]


def configure_blueprint(app, config):
    app.config.from_object(config)

    
# test
def configure_hook(app):
    # log every incoming requests
    @app.before_request
    def before_request():
        app.logger.debug("Hitting %s" % flask.request.url)


def configure_blueprints(app, blueprints):
    for blueprint in blueprints:
        app.register_blueprint(blueprint)


def configure_logging(app):
    app.logger.removeHandler(default_handler)


def configure_extensions(app):
    Babel(app)
    # Bcrypt(app)
    # Cache(app)
    Compress(app)
    DebugToolbarExtension(app)
    # FlaskStaticCompress(app)
    minify(app)
    # Talisman(app)
    Themes(app, app_identifier="pyload")


def configure_error_handlers(app):
    """Register error handlers."""

    def render_error(response):
        """Render error template."""
        if response.is_json:
            json_obj = response.get_json()
            error_msg = json_obj.get('error', 'Server Error')
            trace_msg = json_obj.get('traceback', "No Traceback Available").replace("\n", "<br>")
        else:
            error_msg = str(response.data) or 'Server Error'
            trace_msg = "No Traceback Available"
        
        app.logger.error("Error {}: {}".format(response.status, error_msg))
        
        messages = [response.status, error_msg, trace_msg]
        return render_template("error.html", {"messages": messages}, [pre_processor]), response.status_code

    for errcode in BAD_HTTP_STATUS_CODES:
        app.register_error_handler(errcode, render_error)


def configure_jinja_env(app):
    userdir = app.config["PYLOAD_API"].get_userdir()
    cache_path = os.path.join(userdir, ".tmp", "jinja")
    
    os.makedirs(cache_path, exist_ok=True)

    app.create_jinja_environment()
    app.jinja_env.bytecode_cache = jinja2.FileSystemBytecodeCache(cache_path)
    app.jinja_env.filters.update(JINJA_FILTERS)


def create_app(api, debug=False):
    """Run Flask server"""
    app = flask.Flask(__name__.split(".")[0], root_path=FLASK_ROOT_PATH)
    app.config["PYLOAD_API"] = api

    config = get_config(debug)
    blueprints = DEFAULT_BLUEPRINTS

    configure_blueprint(app, config)
    # configure_hook(app)
    configure_blueprints(app, blueprints)
    configure_extensions(app)
    configure_logging(app)
    configure_error_handlers(app)
    configure_jinja_env(app)

    return app
