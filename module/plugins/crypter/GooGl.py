# -*- coding: utf-8 -*-

from module.plugins.Crypter import Crypter
from module.common.json_layer import json_loads


class GooGl(Crypter):
    __name__    = "GooGl"
    __type__    = "crypter"
    __version__ = "0.01"

    __pattern__ = r'https?://(?:www\.)?goo\.gl/\w+'
    __config__  = [("use_subfolder", "bool", "Save package to subfolder", True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description__ = """Goo.gl decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it")]


    API_URL = "https://www.googleapis.com/urlshortener/v1/url"


    def decrypt(self, pyfile):
        rep = self.load(self.API_URL, get={'shortUrl': pyfile.url})
        self.logDebug("JSON data: " + rep)
        rep = json_loads(rep)

        if 'longUrl' in rep:
            self.urls = [rep['longUrl']]
        else:
            self.fail(_("Unable to expand shortened link"))
