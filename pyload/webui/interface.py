#!/usr/bin/env python
# -*- coding: utf-8 -*-
#@author: RaNaN

from __future__ import absolute_import, unicode_literals

import sys
from os.path import abspath, dirname, exists, join

import bottle
# Middlewares
from beaker.middleware import SessionMiddleware
from bottle import app, run

from pyload.thread import webserver as ServerThread
from pyload.utils.jsengine import JsEngine
# Last routes to register,
from pyload.webui import api, cnl, pyload, setup
from pyload.webui.middlewares import PrefixMiddleware, StripPathMiddleware

APP_DIR = abspath(join(dirname(__file__), 'app'))
PYLOAD_DIR = abspath(join(APP_DIR, '..', '..', '..'))



SETUP = None
PYLOAD = None


if not ServerThread.core:
    if ServerThread.setup:
        SETUP = ServerThread.setup
        config = SETUP.config
    else:
        raise Exception("Could not access pyLoad Core")
else:
    PYLOAD = ServerThread.core.api
    config = ServerThread.core.config

JS = JsEngine()

TEMPLATE = "default"
DL_ROOT = config.get('general', 'storage_folder')
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

DEBUG = config.get(
    'webui', 'debug') or "-d" in sys.argv or "--debug" in sys.argv
bottle.debug(DEBUG)



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


# Server Adapter


def run_server(host, port, server):
    run(app=web, host=host, port=port, quiet=True, server=server)


if __name__ == "__main__":
    run(app=web, port=8010)
