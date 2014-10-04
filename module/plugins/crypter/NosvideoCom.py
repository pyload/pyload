# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleCrypter import SimpleCrypter


class NosvideoCom(SimpleCrypter):
    __name__ = "NosvideoCom"
    __type__ = "crypter"
    __version__ = "0.01"

    __pattern__ = r'http://(?:www\.)?nosvideo\.com/\?v=\w+'

    __description__ = """Nosvideo.com decrypter plugin"""
    __author_name__ = "igel"
    __author_mail__ = "igelkun@myopera.com"

    LINK_PATTERN = r'href="(http://(?:w{3}\.)?nosupload.com/\?d=\w+)"'
    TITLE_PATTERN = r'<[tT]itle>Watch (?P<title>.+)</[tT]itle>'
