#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: RaNaN

from __future__ import absolute_import, division, unicode_literals

import os
import sys

import bottle
# Middlewares
from beaker.middleware import SessionMiddleware
from future import standard_library

from pyload.core.thread import webserver as ServerThread  # TODO: Recheck...
from pyload.utils.web.middleware import PrefixMiddleware, StripPathMiddleware
# Last routes to register
from pyload.webui import api, cnl, pyload, setup

standard_library.install_aliases()

WEBDIR = os.path.abspath(os.path.join(os.path.dirname(__file__)))
APPDIR = os.path.join(WEBDIR, 'app')

SETUP = None
API = None

if not ServerThread.core:
    if ServerThread.setup:
        SETUP = ServerThread.setup
        config = SETUP.config
    else:
        raise Exception("Could not access pyLoad Core")
else:
    API = ServerThread.core.api
    config = ServerThread.core.config

TEMPLATE = "default"
DL_ROOT = config.get('general', 'storage_folder')
PREFIX = config.get('webui', 'prefix')

if PREFIX:
    PREFIX = PREFIX.rstrip("/")
    if PREFIX and not PREFIX.startswith("/"):
        PREFIX = "/{0}".format(PREFIX)

# APP_PATH = "app"
UNAVAILALBE = True

# webui build is available
if os.path.exists(os.path.join(WEBDIR, "node_modules")):
    UNAVAILALBE = False
if os.path.exists(os.path.join(WEBDIR, "min", "index.html")):
    APPDIR = os.path.join(WEBDIR, 'min')
    
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


if __name__ == '__main__':
    bottle.run(app=web, port=8010)
