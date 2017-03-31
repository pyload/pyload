# -*- coding: utf-8 -*-
# @author: vuolter

from __future__ import absolute_import, unicode_literals

import bottle
from future import standard_library
standard_library.install_aliases()


__all__ = ['auto', 'fastcgi', 'lightweight', 'threaded']


def auto(app, host, port, key=None, cert=None):
    bottle.run(app=app, host=host, port=port, server="auto", quiet=True,
               certfile=cert, keyfile=key)


def lightweight(app, host, port, key=None, cert=None):
    bottle.run(app=app, host=host, port=port, server="bjoern", quiet=True,
               reuse_port=True)


def threaded(app, host, port, key=None, cert=None):
    bottle.run(app=app, host=host, port=port, server="cherrypy", quiet=True,
               certfile=cert, keyfile=key)


def fastcgi(app, host, port, key=None, cert=None):
    bottle.run(app=app, host=host, port=port, server="flup", quiet=True,
               certfile=cert, keyfile=key)
