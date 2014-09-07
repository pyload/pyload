import re

from pyload.plugins.internal.SimpleCrypter import SimpleCrypter
from pyload.utils import uniqify


class ImgurComAlbum(SimpleCrypter):
    __name__ = "ImgurComAlbum"
    __type__ = "crypter"
    __version__ = "0.4"

    __pattern__ = r'https?://(?:www\.|m\.)?imgur\.com/(a|gallery|)/?\w{5,7}'

    __description__ = """Imgur.com decrypter plugin"""
    __author_name_ = "nath_schwarz"
    __author_mail_ = "nathan.notwhite@gmail.com"

    TITLE_PATTERN = r'(?P<title>.+) - Imgur'
    LINK_PATTERN = r'i\.imgur\.com/\w{7}s?\.(?:jpeg|jpg|png|gif|apng)'


    def getLinks(self):
        f = lambda url: "http://" + re.sub(r'(\w{7})s\.', r'\1.', url)
        return uniqify(map(f, re.findall(self.LINK_PATTERN, self.html)))
