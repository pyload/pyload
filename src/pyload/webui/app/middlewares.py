# -*- coding: utf-8 -*-

from builtins import object


class StripPathMiddleware(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, e, h):
        e["PATH_INFO"] = e["PATH_INFO"].rstrip("/")
        return self.app(e, h)


class PrefixMiddleware(object):
    def __init__(self, app, prefix="/pyload"):
        self.app = app
        self.prefix = prefix

    def __call__(self, e, h):
        path = e["PATH_INFO"]
        if path.startswith(self.prefix):
            e["PATH_INFO"] = path.replace(self.prefix, "", 1)
        return self.app(e, h)
