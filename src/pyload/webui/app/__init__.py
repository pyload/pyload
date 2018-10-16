#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: RaNaN

import os
import sys
from builtins import str, PKGDIR

import bottle
import pyload.utils.pylgettext as gettext
from beaker.middleware import SessionMiddleware
import bottle
import jinja2
from pyload.utils.utils import decode, formatSize
import json
from pyload.webui.server_thread import PYLOAD_API

from pyload.webui.app.middlewares import (
    GZipMiddleWare,
    PrefixMiddleware,
    StripPathMiddleware,
)

PREFIX = PYLOAD_API.getConfigValue("webui", "prefix")

if PREFIX:
    PREFIX = "{}/".format(PREFIX.strip("/"))

bottle.debug(PYLOAD_API.getConfigValue("general", "debug_mode"))

bcc = jinja2.FileSystemBytecodeCache()  #: handle tmp folder
loader = jinja2.FileSystemLoader(os.path.join(PKGDIR, "webui", "themes"))
env = jinja2.Environment(
    loader=loader,
    extensions=["jinja2.ext.i18n", "jinja2.ext.autoescape"],
    trim_blocks=True,
    auto_reload=False,
    bytecode_cache=bcc,
)

from pyload.webui.app.filters import (
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
    os.path.join(PKGDIR, "locale"),
    languages=[PYLOAD_API.getConfigValue("general", "language"), "en"],
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


def run_builtin(host="0.0.0.0", port="8000"):
    bottle.run(app=web, host=host, port=port, quiet=True)


def run_auto(host="0.0.0.0", port="8000"):
    bottle.run(app=web, host=host, port=port, server="auto", quiet=True)


def run_lightweight(host="0.0.0.0", port="8000"):
    bottle.run(app=web, host=host, port=port, server="bjoern", quiet=True)


def run_threaded(host="0.0.0.0", port="8000", theads=3, cert="", key=""):
    bottle.run(
        app=web,
        host=host,
        port=port,
        server="cherrypy",
        quiet=True,
        ssl_certificate=cert,
        ssl_private_key=key,
    )


def run_fcgi(host="0.0.0.0", port="8000"):
    bottle.run(app=web, host=host, port=port, server=bottle.FlupFCGIServer, quiet=True)
