# -*- coding: utf-8 -*-

import re

from pyload.network.RequestFactory import getURL
from pyload.plugin.internal.SimpleHoster import SimpleHoster


class WebshareCz(SimpleHoster):
    __name    = "WebshareCz"
    __type    = "hoster"
    __version = "0.16"

    __pattern = r'https?://(?:www\.)?webshare\.cz/(?:#/)?file/(?P<ID>\w+)'
    __config  = [("use_premium", "bool", "Use premium account if available", True)]

    __description = """WebShare.cz hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("stickell", "l.stickell@yahoo.it"),
                       ("rush", "radek.senfeld@gmail.com")]


    @classmethod
    def getInfo(cls, url="", html=""):
        info = super(WebshareCz, cls).getInfo(url, html)

        if url:
            info['pattern'] = re.match(cls.__pattern, url).groupdict()

            api_data = getURL("https://webshare.cz/api/file_info/",
                              post={'ident': info['pattern']['ID']},
                              decode=True)

            if 'File not found' in api_data:
                info['status'] = 1
            else:
                info['status'] = 2
                info['name']   = re.search('<name>(.+)</name>', api_data).group(1) or info['name']
                info['size']   = re.search('<size>(.+)</size>', api_data).group(1) or info['size']

        return info


    def handle_free(self, pyfile):
        wst = self.account.infos['wst'] if self.account and 'wst' in self.account.infos else ""

        api_data = getURL('https://webshare.cz/api/file_link/',
                          post={'ident': self.info['pattern']['ID'], 'wst': wst},
                          decode=True)

        self.logDebug("API data: " + api_data)

        m = re.search('<link>(.+)</link>', api_data)
        if m is None:
            self.error(_("Unable to detect direct link"))

        self.link = m.group(1)


    def handle_premium(self, pyfile):
        return self.handle_free(pyfile)
