# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleCrypter import create_getInfo
from module.plugins.Crypter import Crypter as _Crypter


class DeadCrypter(_Crypter):
    __name__    = "DeadCrypter"
    __type__    = "crypter"
    __version__ = "0.05"

    __pattern__ = r'^unmatchable$'

    __description__ = """ Crypter is no longer available """
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it")]


    @classmethod
    def apiInfo(cls, url):
        api = super(DeadCrypter, cls).apiInfo(url)
        api['status'] = 1
        return api


    def setup(self):
        self.pyfile.error = "Crypter is no longer available"
        self.offline()  #@TODO: self.offline("Crypter is no longer available")


getInfo = create_getInfo(DeadCrypter)
