# -*- coding: utf-8 -*-
# @author: vuolter

import os
from builtins import str, PKGDIR
import jinja2
from pyload.utils.utils import formatSize




# cache = os.path.join(HOMEDIR, 'pyLoad', '.tmp', 'webui')
# os.makedirs(cache, exist_ok=True)

# bcc = jinja2.FileSystemBytecodeCache(cache)  # TODO: change to TMPDIR
# sp = os.path.join(PKGDIR, "webui", "app", "themes")
# loader = jinja2.FileSystemLoader(sp)
# env = jinja2.Environment(
    # loader=loader,
    # extensions=["jinja2.ext.i18n", "jinja2.ext.autoescape"],
    # trim_blocks=True,
    # auto_reload=False,
    # bytecode_cache=bcc,
# )




# gettext.setpaths([os.path.join(os.sep, "usr", "share", "pyload", "locale"), None])
# translation = gettext.translation(
    # "webui",
    # os.path.join(PKGDIR, "locale"),
    # languages=[PYLOAD_API.getConfigValue("general", "language"), "en"],
    # fallback=True,
# )
# translation.install(True)
# env.install_gettext_translations(translation)



    
    

import flask
from pyload.webui.app.settings import get_config
from flask_themes2 import Themes
# from flask_bcrypt import Bcrypt
# from flask_caching import Cache
# from flask_debugtoolbar import DebugToolbarExtension
from flask_babel import Babel
from pyload.webui.app.blueprints import api_blueprint, cnl_blueprint, json_blueprint, app_blueprint
from pyload.webui.app.filters import (
    date,
    path_make_absolute,
    path_make_relative,
    quotepath,
    truncate,
)

DEFAULT_BLUEPRINTS = [  
   api_blueprint.bp,
   cnl_blueprint.bp,
   json_blueprint.bp,
   app_blueprint.bp
]    

HANDLED_ERROR_CODES = (401, 403, 404, 500)

   
def _configure_blueprint(app, config):  
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
    Babel(app)
    # Bcrypt(app)
    # Cache(app)
    # DebugToolbarExtension(app)
    Themes(app, app_identifier='pyload')
    
    
def _configure_error_handlers(app):  
    """Register error handlers."""
    
    def render_error(error):
        """Render error template."""
        # If a HTTPException, pull the `code` attribute; default to 500
        error_code = getattr(error, 'code', 500)
        return flask.render_template('{0}.html'.format(error_code)), error_code

    for errcode in HANDLED_ERROR_CODES:
        app.errorhandler(errcode)(render_error)
        
        
def _configure_jinja_env(app):
    app.create_jinja_environment()
    app.jinja_env.filters.update({
        "quotepath": quotepath,
        "truncate": truncate,
        "date": date,
        "path_make_relative": path_make_relative,
        "path_make_absolute": path_make_absolute,
        "formatsize": formatSize,
        "getitem": lambda x, y: x.__getitem__(y)
    })
    
    
def create_app(api, debug=False):
    """Run Flask server"""   
    root_path = os.path.join(PKGDIR, "webui", "app")
    app = flask.Flask(__name__.split('.')[0], root_path=root_path)
    app.config['PYLOAD_API'] = api
    
    config = get_config(debug)
    blueprints = DEFAULT_BLUEPRINTS
    
    _configure_blueprint(app, config)
    _configure_hook(app)
    _configure_blueprints(app, blueprints)
    _configure_extensions(app)
    _configure_logging(app)
    _configure_error_handlers(app)
    _configure_jinja_env(app)
    
    return app
        
    # test
    # from flask.logging import default_handler
    # logging.basicConfig(level=logging.DEBUG)
    # app.logger.disabled = True
    # log = logging.getLogger('werkzeug')
    # log.disabled = True
    # app.logger.removeHandler(default_handler)
    