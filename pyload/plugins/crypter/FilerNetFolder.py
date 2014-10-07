import re

from pyload.plugins.internal.SimpleCrypter import SimpleCrypter


class FilerNetFolder(SimpleCrypter):
    __name__ = "FilerNetFolder"
    __type__ = "crypter"
    __version__ = "0.4"

    __pattern__ = r'https?://filer\.net/folder/\w{16}'

    __description__ = """Filer.net decrypter plugin"""
    __authors__ = [("nath_schwarz", "nathan.notwhite@gmail.com"),
                   ("stickell", "l.stickell@yahoo.it")]


    LINK_PATTERN = r'href="(/get/\w{16})">(?!<)'
    TITLE_PATTERN = r'<h3>(.+?) - <small'


    def getLinks(self):
        return ['http://filer.net%s' % link for link in re.findall(self.LINK_PATTERN, self.html)]
