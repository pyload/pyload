# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleCrypter import SimpleCrypter, create_getInfo
from module.plugins.internal.utils import json


class GooGl(SimpleCrypter):
    __name__    = "GooGl"
    __type__    = "crypter"
    __version__ = "0.05"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?goo\.gl/([a-zA-Z]+/)?\w+'
    __config__  = [("activated", "bool", "Activated", True)]

    __description__ = """Goo.gl decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell"      , "l.stickell@yahoo.it"),
                       ("Walter Purcaro", "vuolter@gmail.com"  )]


    API_URL = "https://www.googleapis.com/urlshortener/v1/url"

    OFFLINE_PATTERN = r'has been disabled|does not exist'


    def get_links(self):
        rep = self.load(self.API_URL, get={'shortUrl': self.pyfile.url})
        self.log_debug("JSON data: " + rep)
        rep = json.loads(rep)
        return [rep['longUrl']] if "longUrl" in rep else None


getInfo = create_getInfo(GooGl)
