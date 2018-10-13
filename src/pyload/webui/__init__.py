#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: RaNaN

import os
import sys
from builtins import str

import bottle
import pyload.utils.pylgettext as gettext
from beaker.middleware import SessionMiddleware
import bottle
import jinja2
from pyload.utils.utils import decode, formatSize
from pyload.plugins.utils import json  # change to core utils
from pyload.webui import server_thread, api_app, cnl_app, json_app, pyload_app

from pyload.webui.middlewares import (
    GZipMiddleWare,
    PrefixMiddleware,
    StripPathMiddleware,
)

THEME_DIR  = os.path.abspath(os.path.join(os.path.dirname(__file__), "themes"))
PYLOAD_DIR = os.path.abspath(os.path.join(THEME_DIR, "..", "..", ".."))

sys.path.append(PYLOAD_DIR)


SETUP = None
PYLOAD = None


if not server_thread.core:
    if server_thread.setup:
        SETUP = server_thread.setup
        config = SETUP.config
    else:
        raise Exception("Could not access pyLoad Core")
else:
    PYLOAD = server_thread.core.api
    config = server_thread.core.config

THEME = config.get("webui", "template")
DL_ROOT = config.get("general", "download_folder")
LOG_ROOT = config.get("log", "log_folder")
PREFIX = config.get("webui", "prefix")

if PREFIX:
    PREFIX = PREFIX.rstrip("/")
    if not PREFIX.startswith("/"):
        PREFIX = "/" + PREFIX

DEBUG = config.get("general", "debug_mode") or "-d" in sys.argv or "--debug" in sys.argv
bottle.debug(DEBUG)

cache = os.path.join("tmp", "jinja_cache")
if not os.path.exists(cache):
    os.makedirs(cache)

bcc = jinja2.FileSystemBytecodeCache(cache, "{}.cache")
loader = jinja2.jinja2.FileSystemLoader([THEME_DIR, os.path.join(THEME_DIR, THEME)])

env = jinja2.Environment(
    loader=loader,
    extensions=["jinja2.ext.i18n", "jinja2.ext.autoescape"],
    trim_blocks=True,
    auto_reload=False,
    bytecode_cache=bcc,
)

from pyload.webui.filters import (
    date,
    path_make_absolute,
    path_make_relative,
    quotepath,
    truncate,
)

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

gettext.setpaths([os.path.join(os.sep, "usr", "share", "pyload", "locale"), None])
translation = gettext.translation(
    "webui",
    os.path.join(PYLOAD_DIR, "locale"),
    languages=[config.get("general", "language"), "en"],
    fallback=True,
)
translation.install(True)
env.install_gettext_translations(translation)


session_opts = {
    "session.type": "file",
    "session.cookie_expires": False,
    "session.data_dir": "./tmp",
    "session.auto": False,
}

web = StripPathMiddleware(SessionMiddleware(bottle.app(), session_opts))
web = GZipMiddleWare(web)

if PREFIX:
    web = PrefixMiddleware(web, prefix=PREFIX)

from pyload.webui import app
def run_builtin(host="0.0.0.0", port="8000"):
    bottle.run(app=web, host=host, port=port, quiet=True)

    
def run_auto(host="0.0.0.0", port="8000"):
    bottle.run(app=web, host=host, port=port, server="auto", quiet=True)


def run_lightweight(host="0.0.0.0", port="8000"):
    bottle.run(app=web, host=host, port=port, server="bjoern", quiet=True)


def run_threaded(host="0.0.0.0", port="8000", theads=3, cert="", key=""):
    from wsgiserver import CherryPyWSGIServer

    if cert and key:
        CherryPyWSGIServer.ssl_certificate = cert
        CherryPyWSGIServer.ssl_private_key = key

    CherryPyWSGIServer.numthreads = theads

    from pyload.webui.app.utils import CherryPyWSGI

    bottle.run(app=web, host=host, port=port, server=CherryPyWSGI, quiet=True)


def run_fcgi(host="0.0.0.0", port="8000"):
    bottle.run(app=web, host=host, port=port, server=bottle.FlupFCGIServer, quiet=True)
