#!/usr/bin/env python
# -*- coding: utf-8 -*-
#@author: RaNaN

from __future__ import absolute_import
from __future__ import unicode_literals
import sys

from os.path import join, abspath, dirname, exists

APP_DIR = abspath(join(dirname(__file__), 'app'))
PYLOAD_DIR = abspath(join(APP_DIR, '..', '..', '..'))

import bottle
from bottle import run, app

from pyload.webui.middlewares import StripPathMiddleware, PrefixMiddleware

SETUP = None
PYLOAD = None

from pyload.thread import server as ServerThread

if not ServerThread.core:
    if ServerThread.setup:
        SETUP = ServerThread.setup
        config = SETUP.config
    else:
        raise Exception("Could not access pyLoad Core")
else:
    PYLOAD = ServerThread.core.api
    config = ServerThread.core.config

from pyload.utils.jsengine import JsEngine
JS = JsEngine()

TEMPLATE = config.get('webui', 'template')
DL_ROOT = config.get('general', 'download_folder')
PREFIX = config.get('webui', 'prefix')

if PREFIX:
    PREFIX = PREFIX.rstrip("/")
    if PREFIX and not PREFIX.startswith("/"):
        PREFIX = "/{}".format(PREFIX)

# APP_PATH = "app"
UNAVAILALBE = True

# webui build is available
if exists(join(APP_DIR, "modules")):
    UNAVAILALBE = False
elif exists(join(APP_DIR, "dist", "index.html")):
    # APP_PATH = "dist"
    UNAVAILALBE = False

DEBUG = config.get("general", "debug_mode") or "-d" in sys.argv or "--debug" in sys.argv
bottle.debug(DEBUG)


# Middlewares
from beaker.middleware import SessionMiddleware

session_opts = {
    'session.type': 'file',
    'session.cookie_expires': False,
    'session.data_dir': './tmp',
    'session.auto': False
}

session = SessionMiddleware(app(), session_opts)
web = StripPathMiddleware(session)

if PREFIX:
    web = PrefixMiddleware(web, prefix=PREFIX)

from pyload.webui import api
from pyload.webui import cnl
from pyload.webui import setup
# Last routes to register,
from pyload.webui import pyload

# Server Adapter
def run_server(host, port, server):
    run(app=web, host=host, port=port, quiet=True, server=server)


if __name__ == "__main__":
    run(app=web, port=8010)
