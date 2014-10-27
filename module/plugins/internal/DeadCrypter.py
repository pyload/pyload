# -*- coding: utf-8 -*-

from module.plugins.Crypter import Crypter as _Crypter


class DeadCrypter(_Crypter):
    __name__    = "DeadCrypter"
    __type__    = "crypter"
    __version__ = "0.02"

    __pattern__ = None
    __config__  = []

    __description__ = """ Crypter is no longer available """
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it")]


    def setup(self):
        self.pyfile.error = "Crypter is no longer available"
        self.offline()  #@TODO: self.offline("Crypter is no longer available")
