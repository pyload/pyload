# -*- coding: utf-8 -*-

import re

from module.network.RequestFactory import getURL
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class WebshareCz(SimpleHoster):
    __name__    = "WebshareCz"
    __type__    = "hoster"
    __version__ = "0.16"

    __pattern__ = r'https?://(?:www\.)?webshare\.cz/(?:#/)?file/(?P<ID>\w+)'

    __description__ = """WebShare.cz hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it"),
                       ("rush", "radek.senfeld@gmail.com")]


    @classmethod
    def getInfo(cls, url="", html=""):
        info = super(WebshareCz, cls).getInfo(url, html)

        if url:
            info['pattern'] = re.match(cls.__pattern__, url).groupdict()

            api_data = getURL("https://webshare.cz/api/file_info/",
                              post={'ident': info['pattern']['ID']},
                              decode=True)

            if 'File not found' in api_data:
                info['status'] = 1
            else:
                info["status"] = 2
                info['name']   = re.search('<name>(.+)</name>', api_data).group(1) or info['name']
                info['size']   = re.search('<size>(.+)</size>', api_data).group(1) or info['size']

        return info


    def handleFree(self, pyfile):
        wst = self.account.infos['wst'] if self.account and 'wst' in self.account.infos else ""

        api_data = getURL('https://webshare.cz/api/file_link/',
                          post={'ident': self.info['pattern']['ID'], 'wst': wst},
                          decode=True)

        self.logDebug("API data: " + api_data)

        m = re.search('<link>(.+)</link>', api_data)
        if m is None:
            self.error(_("Unable to detect direct link"))

        self.link = m.group(1)


    def handlePremium(self, pyfile):
        return self.handleFree(pyfile)


getInfo = create_getInfo(WebshareCz)
