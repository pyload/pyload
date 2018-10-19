#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: RaNaN, vuolter

import os
import sys
from builtins import str, PKGDIR

import flask
import flask_themes2

import pyload.utils.pylgettext as gettext
from beaker.middleware import SessionMiddleware
import jinja2
from pyload.utils.utils import formatSize
import json
from pyload.webui.server_thread import PYLOAD_API

from pyload.webui.app.middlewares import (
    PrefixMiddleware,
    StripPathMiddleware,
)

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

from pyload.webui.app.filters import (
    date,
    path_make_absolute,
    path_make_relative,
    quotepath,
    truncate,
)

env.filters["quotepath"] = quotepath
env.filters["truncate"] = truncate
env.filters["date"] = date
env.filters["path_make_relative"] = path_make_relative
env.filters["path_make_absolute"] = path_make_absolute
env.filters["formatsize"] = formatSize
env.filters["getitem"] = lambda x, y: x.__getitem__(y)
env.filters["url"] = lambda x: PREFIX + x if x.startswith("/") else x

gettext.setpaths([os.path.join(os.sep, "usr", "share", "pyload", "locale"), None])
translation = gettext.translation(
    "webui",
    os.path.join(PKGDIR, "locale"),
    languages=[PYLOAD_API.getConfigValue("general", "language"), "en"],
    fallback=True,
)
translation.install(True)
env.install_gettext_translations(translation)


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


    
    
def create_app():
    app = flask.Flask(__name__.split('.')[0])
    # app = Flask(__name__, template_folder='views',static_folder='public/static')
    
    from pyload.webui.app import api_app, cnl_app, json_app
    app.register_blueprint(api_app.bp)
    app.register_blueprint(cnl_app.bp)
    app.register_blueprint(json_app.bp)
    
    flask_themes2.Themes(app, app_identifier='pyload')
    return app
    
    
def run_flask(host='0.0.0.0', port='8000', debug=False):
    """Run Flask server."""    
    app = create_app()
    
    # with app.app_context():
        # flask.init_db()
        
    app.run(
        host=host,
        port=port,
        use_reloader=False,
        debug=debug
    )
    
# def run_wgsi(host="0.0.0.0", port="8000", debug=False):
    # bottle.run(app=web, host=host, port=port, quiet=True, debug=debug)


# def run_auto(host="0.0.0.0", port="8000", debug=False):
    # bottle.run(app=web, host=host, port=port, server="auto", quiet=True, debug=debug)


# def run_bjoern(host="0.0.0.0", port="8000", debug=False):
    # bottle.run(app=web, host=host, port=port, server="bjoern", quiet=True, debug=debug)


# def run_cherrypy(host="0.0.0.0", port="8000", debug=False, theads=3, cert="", key=""):
    # bottle.run(
        # app=web,
        # host=host,
        # port=port,
        # server="cherrypy",
        # quiet=True,
        # ssl_certificate=cert,
        # ssl_private_key=key,
        # debug=debug
    # )
    

# def run_fcgi(host="0.0.0.0", port="8000", debug=False):
    # bottle.run(app=web, host=host, port=port, server=bottle.FlupFCGIServer, quiet=True, debug=debug)
