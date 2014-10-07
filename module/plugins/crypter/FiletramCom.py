# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleCrypter import SimpleCrypter


class FiletramCom(SimpleCrypter):
    __name__ = "FiletramCom"
    __type__ = "crypter"
    __version__ = "0.02"

    __pattern__ = r'http://(?:www\.)?filetram.com/[^/]+/.+'

    __description__ = """Filetram.com decrypter plugin"""
    __author_name__ = ("igel", "stickell")
    __author_mail__ = ("igelkun@myopera.com", "l.stickell@yahoo.it")

    LINK_PATTERN = r'\s+(http://.+)'
    TITLE_PATTERN = r'<title>(.+?) - Free Download'
