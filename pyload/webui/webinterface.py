#!/usr/bin/env python
# -*- coding: utf-8 -*-
#@author: RaNaN

from __future__ import absolute_import
from __future__ import unicode_literals
import sys

from os.path import join, abspath, dirname, exists

PROJECT_DIR = abspath(dirname(__file__))
PYLOAD_DIR = abspath(join(PROJECT_DIR, "..", ".."))

import bottle
from bottle import run, app

from .middlewares import StripPathMiddleware, PrefixMiddleware

SETUP = None
PYLOAD = None

from . import serverthread as ServerThread

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
        PREFIX = "/" + PREFIX

APP_PATH = "app"
UNAVAILALBE = True

# webui build is available
if exists(join(PROJECT_DIR, "node_modules")) and exists(join(PROJECT_DIR, ".tmp")):
    UNAVAILALBE = False
elif exists(join(PROJECT_DIR, "dist", "index.html")):
    APP_PATH = "dist"
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

from . import api_app
from . import cnl_app
from . import setup_app
# Last routes to register,
from . import pyload_app

# Server Adapter
def run_server(host, port, server):
    run(app=web, host=host, port=port, quiet=True, server=server)


if __name__ == "__main__":
    run(app=web, port=8001)
