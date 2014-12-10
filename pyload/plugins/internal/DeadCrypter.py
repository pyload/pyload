# -*- coding: utf-8 -*-

from urllib import unquote
from urlparse import urlparse

from pyload.plugins.Crypter import Crypter as _Crypter
from pyload.plugins.internal.SimpleCrypter import create_getInfo


class DeadCrypter(_Crypter):
    __name    = "DeadCrypter"
    __type    = "crypter"
    __version = "0.04"

    __pattern = r'^unmatchable$'

    __description = """Crypter is no longer available"""
    __license     = "GPLv3"
    __authors     = [("stickell", "l.stickell@yahoo.it")]


    @classmethod
    def getInfo(cls, url="", html=""):
        return {'name': urlparse(unquote(url)).path.split('/')[-1] or _("Unknown"), 'size': 0, 'status': 1, 'url': url}


    def setup(self):
        self.pyfile.error = "Crypter is no longer available"
        self.offline()  #@TODO: self.offline("Crypter is no longer available")


getInfo = create_getInfo(DeadCrypter)
