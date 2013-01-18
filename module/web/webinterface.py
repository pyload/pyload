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
import module.common.pylgettext as gettext

import os
from os.path import join, abspath, dirname, exists
from os import makedirs

PROJECT_DIR = abspath(dirname(__file__))
PYLOAD_DIR = abspath(join(PROJECT_DIR, "..", ".."))

sys.path.append(PYLOAD_DIR)

from module import InitHomeDir
from module.utils import format_size

import bottle
from bottle import run, app

from jinja2 import Environment, FileSystemLoader, PrefixLoader, FileSystemBytecodeCache
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

from module.common.JsEngine import JsEngine

JS = JsEngine()

TEMPLATE = config.get('webinterface', 'template')
DL_ROOT = config.get('general', 'download_folder')
LOG_ROOT = config.get('log', 'log_folder')
PREFIX = config.get('webinterface', 'prefix')

if PREFIX:
    PREFIX = PREFIX.rstrip("/")
    if PREFIX and not PREFIX.startswith("/"):
        PREFIX = "/" + PREFIX

DEBUG = config.get("general", "debug_mode") or "-d" in sys.argv or "--debug" in sys.argv
bottle.debug(DEBUG)

cache = join("tmp", "jinja_cache")
if not exists(cache):
    makedirs(cache)

bcc = FileSystemBytecodeCache(cache, '%s.cache')
loader = PrefixLoader({
    "default": FileSystemLoader(join(PROJECT_DIR, "templates", "default")),
    "mobile": FileSystemLoader(join(PROJECT_DIR, "templates", "mobile")),
    'js': FileSystemLoader(join(PROJECT_DIR, 'media', 'js'))
})

env = Environment(loader=loader, extensions=['jinja2.ext.i18n', 'jinja2.ext.autoescape'], trim_blocks=True, auto_reload=True,
    bytecode_cache=bcc)

# Filter

env.filters["type"] = lambda x: str(type(x))
env.filters["formatsize"] = format_size
env.filters["getitem"] = lambda x, y: x.__getitem__(y)
if not PREFIX:
    env.filters["url"] = lambda x: x
else:
    env.filters["url"] = lambda x: PREFIX + x if x.startswith("/") else x

# Locale

gettext.setpaths([join(os.sep, "usr", "share", "pyload", "locale"), None])
translation = gettext.translation("django", join(PYLOAD_DIR, "locale"),
    languages=[config.get("general", "language"), "en"],fallback=True)
translation.install(True)
env.install_gettext_translations(translation)

# Middlewares

from beaker.middleware import SessionMiddleware

session_opts = {
    'session.type': 'file',
    'session.cookie_expires': False,
    'session.data_dir': './tmp',
    'session.auto': False
}

web = StripPathMiddleware(SessionMiddleware(app(), session_opts))
web = GZipMiddleWare(web)

if PREFIX:
    web = PrefixMiddleware(web, prefix=PREFIX)

import pyload_app
import setup_app
import cnl_app
import api_app

# Server Adapter
def run_server(host, port, server):
    run(app=web, host=host, port=port, quiet=True, server=server)

if __name__ == "__main__":
    run(app=web, port=8001)
