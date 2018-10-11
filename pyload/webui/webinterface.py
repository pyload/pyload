#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: RaNaN

import os
import sys
from builtins import str
from os import makedirs
from os.path import abspath, dirname, exists, join

import bottle
import pyload.utils.pylgettext as gettext
from beaker.middleware import SessionMiddleware
from bottle import app, run
from jinja2 import Environment, FileSystemBytecodeCache, FileSystemLoader, PrefixLoader
from pyload import InitHomeDir
from pyload.utils.JsEngine import JsEngine
from pyload.utils.json_layer import json
from pyload.utils.utils import decode, formatSize
from pyload.webui import ServerThread, api_app, cnl_app, json_app, pyload_app
from pyload.webui.filters import (date, path_make_absolute, path_make_relative,
                                  quotepath, truncate)
from pyload.webui.middlewares import (GZipMiddleWare, PrefixMiddleware,
                                      StripPathMiddleware)

PROJECT_DIR = abspath(dirname(__file__))
PYLOAD_DIR = abspath(join(PROJECT_DIR, "..", ".."))

sys.path.append(PYLOAD_DIR)


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

TEMPLATE = config.get("webinterface", "template")
DL_ROOT = config.get("general", "download_folder")
LOG_ROOT = config.get("log", "log_folder")
PREFIX = config.get("webinterface", "prefix")

if PREFIX:
    PREFIX = PREFIX.rstrip("/")
    if not PREFIX.startswith("/"):
        PREFIX = "/" + PREFIX

DEBUG = config.get("general", "debug_mode") or "-d" in sys.argv or "--debug" in sys.argv
bottle.debug(DEBUG)

cache = join("tmp", "jinja_cache")
if not exists(cache):
    makedirs(cache)

bcc = FileSystemBytecodeCache(cache, "{}.cache")

mapping = {"js": FileSystemLoader(join(PROJECT_DIR, "media", "js"))}
for template in os.listdir(join(PROJECT_DIR, "templates")):
    if os.path.isdir(join(PROJECT_DIR, "templates", template)):
        mapping[template] = FileSystemLoader(join(PROJECT_DIR, "templates", template))

loader = PrefixLoader(mapping)

env = Environment(
    loader=loader,
    extensions=["jinja2.ext.i18n", "jinja2.ext.autoescape"],
    trim_blocks=True,
    auto_reload=False,
    bytecode_cache=bcc,
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

gettext.setpaths([join(os.sep, "usr", "share", "pyload", "locale"), None])
translation = gettext.translation(
    "django",
    join(PYLOAD_DIR, "locale"),
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

web = StripPathMiddleware(SessionMiddleware(app(), session_opts))
web = GZipMiddleWare(web)

if PREFIX:
    web = PrefixMiddleware(web, prefix=PREFIX)


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

    from pyload.webui.utils import CherryPyWSGI

    run(app=web, host=host, port=port, server=CherryPyWSGI, quiet=True)


def run_fcgi(host="0.0.0.0", port="8000"):
    from bottle import FlupFCGIServer

    run(app=web, host=host, port=port, server=FlupFCGIServer, quiet=True)


if __name__ == "__main__":
    run(app=web, port=8001)
