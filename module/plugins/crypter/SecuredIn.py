# -*- coding: utf-8 -*-

from module.plugins.internal.DeadCrypter import DeadCrypter, create_getInfo


class SecuredIn(DeadCrypter):
    __name__    = "SecuredIn"
    __type__    = "crypter"
    __version__ = "0.24"
    __status__  = "stable"

    __pattern__ = r'http://(?:www\.)?secured\.in/download-[\d]+\-\w{8}\.html'
    __config__  = [("activated", "bool", "Activated", True)]

    __description__ = """Secured.in decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("mkaay", "mkaay@mkaay.de")]


getInfo = create_getInfo(SecuredIn)
