# -*- coding: utf-8 -*-

from module.plugins.internal.DeadCrypter import DeadCrypter, create_getInfo


class MBLinkInfo(DeadCrypter):
    __name__    = "MBLinkInfo"
    __type__    = "crypter"
    __version__ = "0.04"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?mblink\.info/?\?id=(\d+)'
    __config__  = []  #@TODO: Remove in 0.4.10

    __description__ = """MBLink.info decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Gummibaer", "Gummibaer@wiki-bierkiste.de"),
                       ("stickell", "l.stickell@yahoo.it")]


getInfo = create_getInfo(MBLinkInfo)
