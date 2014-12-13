# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadCrypter import DeadCrypter, create_getInfo


class MBLinkInfo(DeadCrypter):
    __name    = "MBLinkInfo"
    __type    = "crypter"
    __version = "0.03"

    __pattern = r'http://(?:www\.)?mblink\.info/?\?id=(\d+)'
    __config  = []

    __description = """MBLink.info decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("Gummibaer", "Gummibaer@wiki-bierkiste.de"),
                       ("stickell", "l.stickell@yahoo.it")]


getInfo = create_getInfo(MBLinkInfo)
