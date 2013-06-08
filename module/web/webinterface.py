#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.

    @author: RaNaN
"""

import sys

from os.path import join, abspath, dirname

PROJECT_DIR = abspath(dirname(__file__))
PYLOAD_DIR = abspath(join(PROJECT_DIR, "..", ".."))

sys.path.append(PYLOAD_DIR)

from module import InitHomeDir

import bottle
from bottle import run, app

from middlewares import StripPathMiddleware, GZipMiddleWare, PrefixMiddleware

SETUP = None
PYLOAD = None

from module.web import ServerThread

if not ServerThread.core:
    if ServerThread.setup:
        SETUP = ServerThread.setup
        config = SETUP.config
    else:
        raise Exception("Could not access pyLoad Core")
else:
    PYLOAD = ServerThread.core.api
    config = ServerThread.core.config

from module.utils.JsEngine import JsEngine

JS = JsEngine()

TEMPLATE = config.get('webinterface', 'template')
DL_ROOT = config.get('general', 'download_folder')
PREFIX = config.get('webinterface', 'prefix')
DEVELOP = config.get('webinterface', 'develop')

if PREFIX:
    PREFIX = PREFIX.rstrip("/")
    if PREFIX and not PREFIX.startswith("/"):
        PREFIX = "/" + PREFIX

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
web = GZipMiddleWare(web)

if PREFIX:
    web = PrefixMiddleware(web, prefix=PREFIX)

import api_app
import cnl_app
import setup_app
# Last routes to register,
import pyload_app

# Server Adapter
def run_server(host, port, server):
    run(app=web, host=host, port=port, quiet=True, server=server)


if __name__ == "__main__":
    run(app=web, port=8001)
