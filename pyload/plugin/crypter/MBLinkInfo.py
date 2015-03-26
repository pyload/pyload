# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadCrypter import DeadCrypter


class MBLinkInfo(DeadCrypter):
    __name__    = "MBLinkInfo"
    __type__    = "crypter"
    __version__ = "0.03"

    __pattern__ = r'http://(?:www\.)?mblink\.info/?\?id=(\d+)'
    __config__  = []

    __description__ = """MBLink.info decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Gummibaer", "Gummibaer@wiki-bierkiste.de"),
                       ("stickell", "l.stickell@yahoo.it")]
