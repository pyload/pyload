# -*- coding: utf-8 -*-

from pyload.plugins.internal.Crypter import Crypter as _Crypter


class DeadCrypter(_Crypter):
    __name__    = "DeadCrypter"
    __type__    = "crypter"
    __version__ = "0.02"

    __pattern__ = r'^unmatchable$'

    __description__ = """Crypter is no longer available"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it")]


    def setup(self):
        self.offline("Crypter is no longer available")
