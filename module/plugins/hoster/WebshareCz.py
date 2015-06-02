# -*- coding: utf-8 -*-

import re

from module.network.RequestFactory import getURL
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class WebshareCz(SimpleHoster):
    __name__    = "WebshareCz"
    __type__    = "hoster"
    __version__ = "0.17"

    __pattern__ = r'https?://(?:www\.)?(en\.)?webshare\.cz/(?:#/)?file/(?P<ID>\w+)'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """WebShare.cz hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it    "),
                       ("rush"    , "radek.senfeld@gmail.com")]


    @classmethod
    def apiInfo(cls, url):
        info = super(WebshareCz, cls).apiInfo(url)

        info['pattern'] = re.match(cls.__pattern__, url).groupdict()

        api_data = getURL("https://webshare.cz/api/file_info/",
                          post={'ident': info['pattern']['ID'], 'wst': ""},
                          decode=True)

        if not re.search(r'<status>OK'):
            info['status'] = 1
        else:
            info['status'] = 2
            info['name']   = re.search(r'<name>(.+?)<', api_data).group(1)
            info['size']   = re.search(r'<size>(.+?)<', api_data).group(1)

        return info


    def handleFree(self, pyfile):
        wst = self.account.getAccountData(self.user).get('wst', None) if self.account else None

        api_data = getURL("https://webshare.cz/api/file_link/",
                          post={'ident': self.info['pattern']['ID'], 'wst': wst},
                          decode=True)

        self.logDebug("API data: " + api_data)

        m = re.search('<link>(.+)</link>', api_data)
        if m:
            self.link = m.group(1)


    def handlePremium(self, pyfile):
        return self.handleFree(pyfile)


getInfo = create_getInfo(WebshareCz)
