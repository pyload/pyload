# -*- coding: utf-8 -*-

from module.plugins.internal.DeadCrypter import DeadCrypter


class LofCc(DeadCrypter):
    __name__ = "LofCc"
    __type__ = "crypter"
    __version__ = "0.21"

    __pattern__ = r'http://(?:www\.)?lof.cc/(.*)'

    __description__ = """Lof.cc decrypter plugin"""
    __author_name__ = "mkaay"
    __author_mail__ = "mkaay@mkaay.de"
