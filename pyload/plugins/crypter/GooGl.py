# -*- coding: utf-8 -*-

from pyload.plugins.Crypter import Crypter
from pyload.utils import json_loads


class GooGl(Crypter):
    __name    = "GooGl"
    __type    = "crypter"
    __version = "0.01"

    __pattern = r'https?://(?:www\.)?goo\.gl/\w+'
    __config  = [("use_subfolder", "bool", "Save package to subfolder", True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description = """Goo.gl decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("stickell", "l.stickell@yahoo.it")]


    API_URL = "https://www.googleapis.com/urlshortener/v1/url"


    def decrypt(self, pyfile):
        rep = self.load(self.API_URL, get={'shortUrl': pyfile.url})
        self.logDebug("JSON data: " + rep)
        rep = json_loads(rep)

        if 'longUrl' in rep:
            self.urls = [rep['longUrl']]
        else:
            self.fail(_("Unable to expand shortened link"))
