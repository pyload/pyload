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

from module.common.json_layer import json

import sys
import module.common.pylgettext as gettext

import os
from os.path import join, abspath, dirname, exists
from os import makedirs

PROJECT_DIR = abspath(dirname(__file__))
PYLOAD_DIR = abspath(join(PROJECT_DIR, "..", ".."))

sys.path.append(PYLOAD_DIR)

from module import InitHomeDir
from module.utils import decode, formatSize

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

TEMPLATES = [t for t in os.listdir(os.path.join(pypath, "module", "web", "templates"))
             if os.path.isdir(os.path.join(pypath, "module", "web", "templates", t))]
TEMPLATE = config.get('webinterface', 'template')
if TEMPLATE not in TEMPLATES:
    TEMPLATE = TEMPLATES[0]
config.config['webinterface']['template']['type'] = ';'.join(TEMPLATES)
config.set('webinterface', 'template', TEMPLATE)

DL_ROOT = config.get('general', 'download_folder')
LOG_ROOT = config.get('log', 'log_folder')
PREFIX = config.get('webinterface', 'prefix')

if PREFIX:
    PREFIX = PREFIX.rstrip("/")
    if not PREFIX.startswith("/"):
        PREFIX = "/" + PREFIX

DEBUG = config.get("general", "debug_mode") or "-d" in sys.argv or "--debug" in sys.argv
bottle.debug(DEBUG)

cache = join("tmp", "jinja_cache")
if not exists(cache):
    makedirs(cache)

bcc = FileSystemBytecodeCache(cache, '%s.cache')

mapping = {'js': FileSystemLoader(join(PROJECT_DIR, 'media', 'js'))}
for template in TEMPLATES:
        mapping[template] = FileSystemLoader(join(PROJECT_DIR, "templates", template))

loader = PrefixLoader(mapping)

env = Environment(loader=loader, extensions=['jinja2.ext.i18n', 'jinja2.ext.autoescape'], trim_blocks=True, auto_reload=False,
    bytecode_cache=bcc)

from filters import quotepath, path_make_relative, path_make_absolute, truncate, date

env.filters["tojson"] = json.dumps
env.filters["quotepath"] = quotepath
env.filters["truncate"] = truncate
env.filters["date"] = date
env.filters["path_make_relative"] = path_make_relative
env.filters["path_make_absolute"] = path_make_absolute
env.filters["decode"] = decode
env.filters["type"] = lambda x: str(type(x))
env.filters["formatsize"] = formatSize
env.filters["getitem"] = lambda x, y: x.__getitem__(y)
env.filters["url"] = lambda x: PREFIX + x if x.startswith("/") else x

gettext.setpaths([join(os.sep, "usr", "share", "pyload", "locale"), None])
translation = gettext.translation("django", join(PYLOAD_DIR, "locale"),
    languages=[config.get("general", "language"), "en"],fallback=True)
translation.install(True)
env.install_gettext_translations(translation)

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
import json_app
import cnl_app
import api_app

def run_simple(host="0.0.0.0", port="8000"):
    run(app=web, host=host, port=port, quiet=True)


def run_lightweight(host="0.0.0.0", port="8000"):
    run(app=web, host=host, port=port, quiet=True, server="bjoern")


def run_threaded(host="0.0.0.0", port="8000", theads=3, cert="", key=""):
    from wsgiserver import CherryPyWSGIServer

    if cert and key:
        CherryPyWSGIServer.ssl_certificate = cert
        CherryPyWSGIServer.ssl_private_key = key

    CherryPyWSGIServer.numthreads = theads

    from utils import CherryPyWSGI

    run(app=web, host=host, port=port, server=CherryPyWSGI, quiet=True)


def run_fcgi(host="0.0.0.0", port="8000"):
    from bottle import FlupFCGIServer

    run(app=web, host=host, port=port, server=FlupFCGIServer, quiet=True)


if __name__ == "__main__":
    run(app=web, port=8001)
