# -*- coding: utf-8 -*-

from module.plugins.internal.DeadCrypter import DeadCrypter


class SecuredIn(DeadCrypter):
    __name__ = "SecuredIn"
    __type__ = "container"
    __pattern__ = r"http://[\w\.]*?secured\.in/download-[\d]+-[\w]{8}\.html"
    __version__ = "0.21"
    __description__ = """secured.in Container Plugin"""
    __author_name__ = ("mkaay")
    __author_mail__ = ("mkaay@mkaay.de")
