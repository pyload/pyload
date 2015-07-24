import re

from module.plugins.internal.SimpleCrypter import SimpleCrypter, create_getInfo
from module.utils import uniqify


class ImgurComAlbum(SimpleCrypter):
    __name__    = "ImgurComAlbum"
    __type__    = "crypter"
    __version__ = "0.52"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.|m\.)?imgur\.com/(a|gallery|)/?\w{5,7}'
    __config__  = [("use_premium"       , "bool", "Use premium account if available"   , True),
                   ("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description__ = """Imgur.com decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("nath_schwarz", "nathan.notwhite@gmail.com")]


    NAME_PATTERN = r'(?P<N>.+?) - Imgur'
    LINK_PATTERN = r'i\.imgur\.com/\w{7}s?\.(?:jpeg|jpg|png|gif|apng)'


    def get_links(self):
        f = lambda url: "http://" + re.sub(r'(\w{7})s\.', r'\1.', url)
        return uniqify(map(f, re.findall(self.LINK_PATTERN, self.html)))


getInfo = create_getInfo(ImgurComAlbum)
