# -*- coding: utf-8 -*-

from urllib import unquote
from urlparse import urlparse

from module.plugins.internal.SimpleCrypter import create_getInfo
from module.plugins.Crypter import Crypter as _Crypter


class DeadCrypter(_Crypter):
    __name__    = "DeadCrypter"
    __type__    = "crypter"
    __version__ = "0.04"

    __pattern__ = r'^unmatchable$'

    __description__ = """ Crypter is no longer available """
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it")]


    @classmethod
    def getInfo(cls, url="", html=""):
        return {'name': urlparse(unquote(url)).path.split('/')[-1] or _("Unknown"), 'size': 0, 'status': 1, 'url': url}


    def setup(self):
        self.pyfile.error = "Crypter is no longer available"
        self.offline()  #@TODO: self.offline("Crypter is no longer available")


getInfo = create_getInfo(DeadCrypter)
