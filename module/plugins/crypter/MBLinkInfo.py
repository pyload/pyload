# -*- coding: utf-8 -*-

from module.plugins.internal.DeadCrypter import DeadCrypter


class MBLinkInfo(DeadCrypter):
    __name__ = "MBLinkInfo"
    __version__ = "0.03"
    __type__ = "crypter"

    __pattern__ = r'http://(?:www\.)?mblink\.info/?\?id=(\d+)'

    __description__ = """MBLink.info decrypter plugin"""
    __author_name__ = ("Gummibaer", "stickell")
    __author_mail__ = ("Gummibaer@wiki-bierkiste.de", "l.stickell@yahoo.it")
