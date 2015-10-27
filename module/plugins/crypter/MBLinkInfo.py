# -*- coding: utf-8 -*-

from module.plugins.internal.DeadCrypter import DeadCrypter, create_getInfo


class MBLinkInfo(DeadCrypter):
    __name__    = "MBLinkInfo"
    __type__    = "crypter"
    __version__ = "0.06"
    __status__  = "stable"

    __pattern__ = r'http://(?:www\.)?mblink\.info/?\?id=(\d+)'
    __config__  = [("activated", "bool", "Activated", True)]

    __description__ = """MBLink.info decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Gummibaer", "Gummibaer@wiki-bierkiste.de"),
                       ("stickell", "l.stickell@yahoo.it")]


getInfo = create_getInfo(MBLinkInfo)
