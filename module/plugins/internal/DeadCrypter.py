# -*- coding: utf-8 -*-

from module.plugins.internal.Crypter import Crypter, create_getInfo


class DeadCrypter(Crypter):
    __name__    = "DeadCrypter"
    __type__    = "crypter"
    __version__ = "0.09"
    __status__  = "testing"

    __pattern__ = r'^unmatchable$'

    __description__ = """Crypter is no longer available"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it")]


    @classmethod
    def get_info(cls, *args, **kwargs):
        info = super(DeadCrypter, cls).get_info(*args, **kwargs)
        info['status'] = 1
        return info


    def setup(self):
        self.offline(_("Crypter is no longer available"))


getInfo = create_getInfo(DeadCrypter)
