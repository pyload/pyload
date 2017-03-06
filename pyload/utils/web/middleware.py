# -*- coding: utf-8 -*-
# @author: vuolter

from __future__ import absolute_import, division, unicode_literals

from builtins import object

from future import standard_library

standard_library.install_aliases()


__all__ = ['PrefixMiddleware', 'StripPathMiddleware']


class PrefixMiddleware(object):

    __slots__ = ['app', 'prefix']

    def __init__(self, app, prefix="/pyload"):
        self.app = app
        self.prefix = prefix

    def __call__(self, e, h):
        path = e['PATH_INFO']
        if path.startswith(self.prefix):
            e['PATH_INFO'] = path.replace(self.prefix, "", 1)
        return self.app(e, h)


class StripPathMiddleware(object):

    __slots__ = ['app']

    def __init__(self, app):
        self.app = app

    def __call__(self, e, h):
        e['PATH_INFO'] = e['PATH_INFO'].rstrip('/')
        return self.app(e, h)
