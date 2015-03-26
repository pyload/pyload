import re

from pyload.plugin.internal.SimpleCrypter import SimpleCrypter
from pyload.utils import uniqify


class ImgurComAlbum(SimpleCrypter):
    __name    = "ImgurComAlbum"
    __type    = "crypter"
    __version = "0.51"

    __pattern = r'https?://(?:www\.|m\.)?imgur\.com/(a|gallery|)/?\w{5,7}'
    __config  = [("use_premium"       , "bool", "Use premium account if available"   , True),
                   ("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description = """Imgur.com decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("nath_schwarz", "nathan.notwhite@gmail.com")]


    NAME_PATTERN = r'(?P<N>.+?) - Imgur'
    LINK_PATTERN = r'i\.imgur\.com/\w{7}s?\.(?:jpeg|jpg|png|gif|apng)'


    def getLinks(self):
        f = lambda url: "http://" + re.sub(r'(\w{7})s\.', r'\1.', url)
        return uniqify(map(f, re.findall(self.LINK_PATTERN, self.html)))
