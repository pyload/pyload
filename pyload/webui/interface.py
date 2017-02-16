#!/usr/bin/env python
# -*- coding: utf-8 -*-
#@author: RaNaN

from __future__ import absolute_import, unicode_literals

import os
import sys

import bottle
# Middlewares
from beaker.middleware import SessionMiddleware

from pyload.thread import webserver as ServerThread
from pyload.utils.web.middleware import PrefixMiddleware, StripPathMiddleware
# Last routes to register
from pyload.webui import api, cnl, pyload, setup

APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'app'))
PYLOAD_DIR = os.path.abspath(os.path.join(APP_DIR, '..', '..', '..'))


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
if os.path.exists(os.path.join(APP_DIR, "modules")):
    UNAVAILALBE = False
elif os.path.exists(os.path.join(APP_DIR, "dist", "index.html")):
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

session = SessionMiddleware(bottle.app(), session_opts)
web = StripPathMiddleware(session)

if PREFIX:
    web = PrefixMiddleware(web, prefix=PREFIX)


# Server Adapter


def run_server(host, port, server):
    bottle.run(app=web, host=host, port=port, quiet=True, server=server)


if __name__ == "__main__":
    bottle.run(app=web, port=8010)
