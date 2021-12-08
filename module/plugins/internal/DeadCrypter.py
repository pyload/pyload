# -*- coding: utf-8 -*-

from .Crypter import Crypter


class DeadCrypter(Crypter):
    __name__ = "DeadCrypter"
    __type__ = "crypter"
    __version__ = "0.15"
    __status__ = "stable"

    __pattern__ = r'^unmatchable$'
    __config__ = [("activated", "bool", "Activated", True)]

    __description__ = """Crypter is no longer available"""
    __license__ = "GPLv3"
    __authors__ = [("stickell", "l.stickell@yahoo.it")]

    def get_info(self, *args, **kwargs):
        info = super(DeadCrypter, self).get_info(*args, **kwargs)
        info['status'] = 1
        return info

    def setup(self):
        self.offline(_("Crypter is no longer available"))
