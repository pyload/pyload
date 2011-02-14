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
import gettext

from os.path import join, abspath, dirname, exists
from os import makedirs

PROJECT_DIR = abspath(dirname(__file__))
PYLOAD_DIR = abspath(join(PROJECT_DIR, "..", ".."))

sys.path.append(PYLOAD_DIR)

from module import InitHomeDir

import bottle
from bottle import run, app

from jinja2 import Environment, FileSystemLoader, PrefixLoader, FileSystemBytecodeCache
from middlewares import StripPathMiddleware, GZipMiddleWare

try:
    import module.web.ServerThread

    if not module.web.ServerThread.core:
        raise Exception
    PYLOAD = module.web.ServerThread.core.server_methods
    config = module.web.ServerThread.core.config
except:
    import xmlrpclib

    from module.ConfigParser import ConfigParser
    config = ConfigParser()
    
    class wrap():
        authed = False
        proxy = None
        def checkAuth(self, username, password):
            server_url = "http%s://%s:%s@%s:%s/" % (
              "s" if config.get("ssl", "activated") else "",
              username,
              password,
              config.get("remote", "listenaddr"),
              config.get("remote", "port")
            )
            proxy = xmlrpclib.ServerProxy(server_url, allow_none=True)
            try:
                info = proxy.checkAuth(username, password)
            except:
                self.authed = False
                return {}
            self.proxy = proxy
            self.authed = False
            return info
        
        def __getattr__(self, attr):
            return getattr(self.proxy, attr)
    
    PYLOAD = wrap()

from module.JsEngine import JsEngine

JS = JsEngine()

TEMPLATE = config.get('webinterface', 'template')
DL_ROOT = config.get('general', 'download_folder')
LOG_ROOT = config.get('log', 'log_folder')
DEBUG = config.get("general","debug_mode")
bottle.debug(DEBUG)

bcc = FileSystemBytecodeCache(join("tmp","jinja_cache"))
loader = PrefixLoader({
    "default": FileSystemLoader(join(PROJECT_DIR, "templates", "jinja", "default"))
                      })
env = Environment(loader=loader, extensions=['jinja2.ext.i18n'], trim_blocks=True, auto_reload=False, bytecode_cache=bcc)

from filters import quotepath, path_make_relative, path_make_absolute, truncate,date

env.filters["quotepath"] = quotepath
env.filters["truncate"] = truncate
env.filters["date"] = date
env.filters["path_make_relative"] = path_make_relative
env.filters["path_make_absolute"] = path_make_absolute


translation = gettext.translation("django", join(PROJECT_DIR, "locale"),
                                  languages=["en", config.get("general","language")])
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

import pyload_app
import json_app
import cnl_app


def run_simple(host="0.0.0.0", port="8000"):
    run(app=web, host=host, port=port, quiet=True)

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
