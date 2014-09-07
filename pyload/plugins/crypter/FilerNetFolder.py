import re

from pyload.plugins.internal.SimpleCrypter import SimpleCrypter


class FilerNetFolder(SimpleCrypter):
    __name__ = "FilerNetFolder"
    __type__ = "crypter"
    __version__ = "0.3"

    __pattern__ = r'https?://filer\.net/folder/\w{16}'

    __description__ = """Filer.net decrypter plugin"""
    __author_name_ = ("nath_schwarz", "stickell")
    __author_mail_ = ("nathan.notwhite@gmail.com", "l.stickell@yahoo.it")

    LINK_PATTERN = r'href="(/get/\w{16})">(?!<)'
    TITLE_PATTERN = r'<h3>(?P<title>.+) - <small'


    def getLinks(self):
        return ['http://filer.net%s' % link for link in re.findall(self.LINK_PATTERN, self.html)]
