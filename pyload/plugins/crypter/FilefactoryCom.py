# -*- coding: utf-8 -*-

from pyload.plugins.internal.SimpleCrypter import SimpleCrypter


class FilefactoryCom(SimpleCrypter):
    __name    = "FilefactoryCom"
    __type    = "crypter"
    __version = "0.31"

    __pattern = r'https?://(?:www\.)?filefactory\.com/(?:f|folder)/\w+'
    __config  = [("use_subfolder", "bool", "Save package to subfolder", True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description = """Filefactory.com folder decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("stickell", "l.stickell@yahoo.it")]


    LINK_PATTERN = r'<td><a href="([^"]+)">'
    NAME_PATTERN = r'<h1>Files in <span>(?P<N>.+)</span></h1>'
    PAGES_PATTERN = r'data-paginator-totalPages="(\d+)"'

    COOKIES = [("filefactory.com", "locale", "en_US.utf8")]


    def loadPage(self, page_n):
        return self.load(self.pyfile.url, get={'page': page_n})
