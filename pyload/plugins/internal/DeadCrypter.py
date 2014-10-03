# -*- coding: utf-8 -*-

from pyload.plugins.base.Crypter import Crypter as _Crypter


class DeadCrypter(_Crypter):
    __name__ = "DeadCrypter"
    __type__ = "crypter"
    __version__ = "0.02"

    __pattern__ = None

    __description__ = """Crypter is no longer available"""
    __author_name__ = "stickell"
    __author_mail__ = "l.stickell@yahoo.it"


    def setup(self):
        self.pyfile.error = "Crypter is no longer available"
        self.offline()  #@TODO: self.offline("Crypter is no longer available")
