# -*- coding: utf-8 -*-
# @author: vuolter

import os
# import sys
from builtins import str, PKGDIR

# import pyload.utils.pylgettext as gettext
# from beaker.middleware import SessionMiddleware
import jinja2
# from pyload.utils.utils import formatSize
# import json
from pyload.webui.server_process import PYLOAD_API

# from pyload.webui.app.middlewares import (
    # PrefixMiddleware,
    # StripPathMiddleware,
# )

PREFIX = PYLOAD_API.getConfigValue("webui", "prefix")

if PREFIX:
    PREFIX = "{}/".format(PREFIX.strip("/"))

# bottle.debug(PYLOAD_API.getConfigValue("general", "debug_mode"))

cache = os.path.join(HOMEDIR, 'pyLoad', '.tmp', 'webui')
os.makedirs(cache, exist_ok=True)

bcc = jinja2.FileSystemBytecodeCache(cache)  # TODO: change to TMPDIR
sp = os.path.join(PKGDIR, "webui", "app", "themes")
loader = jinja2.FileSystemLoader(sp)
env = jinja2.Environment(
    loader=loader,
    extensions=["jinja2.ext.i18n", "jinja2.ext.autoescape"],
    trim_blocks=True,
    auto_reload=False,
    bytecode_cache=bcc,
)

# from pyload.webui.app.filters import (
    # date,
    # path_make_absolute,
    # path_make_relative,
    # quotepath,
    # truncate,
# )

# env.filters["quotepath"] = quotepath
# env.filters["truncate"] = truncate
# env.filters["date"] = date
# env.filters["path_make_relative"] = path_make_relative
# env.filters["path_make_absolute"] = path_make_absolute
# env.filters["formatsize"] = formatSize
# env.filters["getitem"] = lambda x, y: x.__getitem__(y)
# env.filters["url"] = lambda x: PREFIX + x if x.startswith("/") else x

# gettext.setpaths([os.path.join(os.sep, "usr", "share", "pyload", "locale"), None])
# translation = gettext.translation(
    # "webui",
    # os.path.join(PKGDIR, "locale"),
    # languages=[PYLOAD_API.getConfigValue("general", "language"), "en"],
    # fallback=True,
# )
# translation.install(True)
# env.install_gettext_translations(translation)


# session_opts = {
    # 'session.type': 'file',
    # 'session.cookie_expires': False,
    # 'session.data_dir': cache,
    # 'session.auto': False
# }

# session = SessionMiddleware(bottle.app(), session_opts)
# web = StripPathMiddleware(session)

# if PREFIX:
    # web = PrefixMiddleware(web, prefix=PREFIX)

    
    

import flask
from pyload.webui.app.settings import get_config
from flask_themes2 import Themes
# from flask_bcrypt import Bcrypt
from flask_caching import Cache
from flask_debugtoolbar import DebugToolbarExtension
# from Flask-Babel import Babel
from pyload.webui.app import api_app, cnl_app, json_app


DEFAULT_BLUEPRINTS = [  
   api_app.bp,
   cnl_app.bp,
   json_app.bp
]    

   
def _configure_app(app, config):  
    app.config.from_object(config)
   
def _configure_hook(app):  
    @app.before_request
    def before_request():
        pass
      
      
def _configure_blueprints(app, blueprints):  
    for blueprint in blueprints:
        app.register_blueprint(blueprint)
        
        
def _configure_logging(app):  
    pass
   
   
def _configure_extensions(app):  
    # Babel(app)
    # Bcrypt(app)
    Cache(app)
    DebugToolbarExtension(app)
    Themes(app, app_identifier='pyload')
    
    
def _configure_error_handlers(app):  
   """Register error handlers."""
    def render_error(error):
        """Render error template."""
        # If a HTTPException, pull the `code` attribute; default to 500
        error_code = getattr(error, 'code', 500)
        return flask.render_template('{0}.html'.format(error_code)), error_code

    for errcode in (401, 404, 500):
        app.errorhandler(errcode)(render_error)
        
        
def _create_app(config, blueprints):    
    app = flask.Flask(__name__.split('.')[0], instance_relative_config=True)
    
    _configure_app(app, config)
    _configure_hook(app)
    _configure_blueprints(app, blueprints)
    _configure_extensions(app)
    _configure_logging(app)
    _configure_error_handlers(app)
    
    return app


def run(host="localhost", port=8001, cert="", key="", debug=False):
    """Run Flask server"""
    config = get_config(debug)
    blueprints = DEFAULT_BLUEPRINTS
    app = _create_app(config, blueprints)
        
    # test
    # from flask.logging import default_handler
    # logging.basicConfig(level=logging.DEBUG)
    # app.logger.disabled = True
    # log = logging.getLogger('werkzeug')
    # log.disabled = True
    # app.logger.removeHandler(default_handler)
    
    try:
        app.run(
            host=host,
            port=port,
            use_reloader=False,
            debug=debug,
            threaded=True,
            use_evalex=False
        )
    finally:
        return app
    
    
def shutdown():
    func = flask.request.environ.get('werkzeug.server.shutdown')
    try:
        func()
    except TypeError:
        raise RuntimeError('Not running with the Werkzeug Server')
