# -*- coding: utf-8 -*-

import re

from module.network.RequestFactory import getURL as get_url
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class WebshareCz(SimpleHoster):
    __name__    = "WebshareCz"
    __type__    = "hoster"
    __version__ = "0.19"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?(en\.)?webshare\.cz/(?:#/)?file/(?P<ID>\w+)'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """WebShare.cz hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it    "),
                       ("rush"    , "radek.senfeld@gmail.com")]


    @classmethod
    def api_info(cls, url):
        info = super(WebshareCz, cls).api_info(url)

        info['pattern'] = re.match(cls.__pattern__, url).groupdict()

        api_data = get_url("https://webshare.cz/api/file_info/",
                           post={'ident': info['pattern']['ID'], 'wst': ""})

        if not re.search(r'<status>OK', api_data):
            info['status'] = 1
        else:
            info['status'] = 2
            info['name']   = re.search(r'<name>(.+?)<', api_data).group(1)
            info['size']   = re.search(r'<size>(.+?)<', api_data).group(1)

        return info


    def handle_free(self, pyfile):
        wst = self.account.get_data(self.user).get('wst', None) if self.account else None

        api_data = get_url("https://webshare.cz/api/file_link/",
                           post={'ident': self.info['pattern']['ID'], 'wst': wst})

        self.log_debug("API data: " + api_data)

        m = re.search('<link>(.+)</link>', api_data)
        if m:
            self.link = m.group(1)


    def handle_premium(self, pyfile):
        return self.handle_free(pyfile)


getInfo = create_getInfo(WebshareCz)
