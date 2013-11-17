# -*- coding: utf-8 -*-

from module.plugins.internal.DeadCrypter import DeadCrypter


class LofCc(DeadCrypter):
    __name__ = "LofCc"
    __type__ = "container"
    __pattern__ = r"http://lof.cc/(.*)"
    __version__ = "0.21"
    __description__ = """lof.cc Plugin"""
    __author_name__ = ("mkaay")
    __author_mail__ = ("mkaay@mkaay.de")
