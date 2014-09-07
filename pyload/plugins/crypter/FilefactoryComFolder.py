# -*- coding: utf-8 -*-

from pyload.plugins.internal.SimpleCrypter import SimpleCrypter


class FilefactoryComFolder(SimpleCrypter):
    __name__ = "FilefactoryComFolder"
    __type__ = "crypter"
    __version__ = "0.2"

    __pattern__ = r'https?://(?:www\.)?filefactory\.com/(?:f|folder)/\w+'

    __description__ = """Filefactory.com folder decrypter plugin"""
    __author_name__ = "stickell"
    __author_mail__ = "l.stickell@yahoo.it"

    LINK_PATTERN = r'<td><a href="([^"]+)">'
    TITLE_PATTERN = r'<h1>Files in <span>(?P<title>.+)</span></h1>'
    PAGES_PATTERN = r'data-paginator-totalPages="(?P<pages>\d+)"'

    SH_COOKIES = [('.filefactory.com', 'locale', 'en_US.utf8')]


    def loadPage(self, page_n):
        return self.load(self.pyfile.url, get={'page': page_n})
