# -*- coding: utf-8 -*-

from module.plugins.Crypter import Crypter
from module.common.json_layer import json_loads


class GooGl(Crypter):
    __name__ = "GooGl"
    __type__ = "crypter"
    __pattern__ = r"https?://(www\.)?goo\.gl/\w+"
    __version__ = "0.01"
    __description__ = """Goo.gl Crypter Plugin"""
    __author_name__ = ("stickell")
    __author_mail__ = ("l.stickell@yahoo.it")

    API_URL = 'https://www.googleapis.com/urlshortener/v1/url'

    def decrypt(self, pyfile):
        rep = self.load(self.API_URL, get={'shortUrl': pyfile.url})
        self.logDebug('JSON data: ' + rep)
        rep = json_loads(rep)

        if 'longUrl' in rep:
            self.core.files.addLinks([rep['longUrl']], self.pyfile.package().id)
        else:
            self.fail('Unable to expand shortened link')
