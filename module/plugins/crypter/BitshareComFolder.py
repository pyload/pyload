# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleCrypter import SimpleCrypter


class BitshareComFolder(SimpleCrypter):
    __name__ = "BitshareComFolder"
    __type__ = "crypter"
    __version__ = "0.02"

    __pattern__ = r'http://(?:www\.)?bitshare\.com/\?d=\w+'

    __description__ = """Bitshare.com folder decrypter plugin"""
    __authors__ = [("stickell", "l.stickell@yahoo.it")]


    LINK_PATTERN = r'<a href="(http://bitshare.com/files/.+)">.+</a></td>'
    TITLE_PATTERN = r'View public folder "(.+)"</h1>'
