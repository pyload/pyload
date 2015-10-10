# -*- coding: utf-8 -*-

from module.plugins.internal.DeadCrypter import DeadCrypter, create_getInfo


class LofCc(DeadCrypter):
    __name__    = "LofCc"
    __type__    = "crypter"
    __version__ = "0.22"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?lof\.cc/(.+)'
    __config__  = []  #@TODO: Remove in 0.4.10

    __description__ = """Lof.cc decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("mkaay", "mkaay@mkaay.de")]


getInfo = create_getInfo(LofCc)
