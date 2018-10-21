# -*- coding: utf-8 -*-
# @author: vuolter

import os
from builtins import str, PKGDIR
import jinja2
from pyload.utils.utils import formatSize
import flask

from pyload.network.http_request import BAD_STATUS_CODES

# from flask_static_compress import FlaskStaticCompress
from flask_minify import minify
from pyload.webui.app.settings import get_config
from flask_themes2 import Themes

# from flask_bcrypt import Bcrypt
# from flask_caching import Cache
from flask_debugtoolbar import DebugToolbarExtension

# from flask_talisman import Talisman
from flask_babel import Babel
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
from pyload.webui.app.utils import render_template


DEFAULT_BLUEPRINTS = [
    api_blueprint.bp,
    cnl_blueprint.bp,
    json_blueprint.bp,
    app_blueprint.bp,
]


def _configure_blueprint(app, config):
    app.config.from_object(config)


def _configure_hook(app):
    # log every incoming requests
    @app.before_request
    def before_request():
        app.logger.debug("Hitting %s" % flask.request.url)


def _configure_blueprints(app, blueprints):
    for blueprint in blueprints:
        app.register_blueprint(blueprint)


def _configure_logging(app):
    pass


def _configure_extensions(app):
    Babel(app)
    # Bcrypt(app)
    # Cache(app)
    DebugToolbarExtension(app)
    # FlaskStaticCompress(app)
    minify(app)
    # Talisman(app)
    Themes(app, app_identifier="pyload")


def _configure_error_handlers(app):
    """Register error handlers."""

    def render_error(error):
        """Render error template."""
        # If a HTTPException, pull the `code` attribute; default to 500
        error_code = getattr(error, "code", 500)
        error_msg = getattr(error, "message", "Internal Server Error")
        messages = (str(error_code), error_msg)
        return render_template("error.html", {"messages": messages}), error_code

    for errcode in BAD_STATUS_CODES:
        app.errorhandler(errcode)(render_error)


def _configure_jinja_env(app):
    cachedir = os.path.join(HOMEDIR, "pyLoad", ".tmp", "jinja")
    os.makedirs(cachedir, exist_ok=True)

    app.create_jinja_environment()
    app.jinja_env.bytecode_cache = jinja2.FileSystemBytecodeCache(cachedir)
    app.jinja_env.filters.update(
        {
            "quotepath": quotepath,
            "truncate": truncate,
            "date": date,
            "path_make_relative": path_make_relative,
            "path_make_absolute": path_make_absolute,
            "formatsize": formatSize,
            "getitem": lambda x, y: x.__getitem__(y),
        }
    )


def create_app(api, debug=False):
    """Run Flask server"""
    rootdir = os.path.join(PKGDIR, "webui", "app")
    app = flask.Flask(__name__.split(".")[0], root_path=rootdir)
    app.config["PYLOAD_API"] = api

    config = get_config(debug)
    blueprints = DEFAULT_BLUEPRINTS

    _configure_blueprint(app, config)
    # _configure_hook(app)
    _configure_blueprints(app, blueprints)
    _configure_extensions(app)
    # _configure_logging(app)
    # _configure_error_handlers(app)
    _configure_jinja_env(app)

    return app
