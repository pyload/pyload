# -*- coding: utf-8 -*-

import re

from module.network.RequestFactory import getURL as get_url
from module.plugins.internal.SimpleHoster import SimpleHoster


class WebshareCz(SimpleHoster):
    __name__    = "WebshareCz"
    __type__    = "hoster"
    __version__ = "0.24"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?(en\.)?webshare\.cz/(?:#/)?(file/)?(?P<ID>\w+)'
    __config__  = [("activated"   , "bool", "Activated"                                        , True),
                   ("use_premium" , "bool", "Use premium account if available"                 , True),
                   ("fallback"    , "bool", "Fallback to free download if premium fails"       , True),
                   ("chk_filesize", "bool", "Check file size"                                  , True),
                   ("max_wait"    , "int" , "Reconnect if waiting time is greater than minutes", 10  )]

    __description__ = """WebShare.cz hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it"    ),
                       ("rush"    , "radek.senfeld@gmail.com"),
                       ("ondrej"  , "git@ondrej.it"          ),]


    @classmethod
    def api_info(cls, url):
        info = {}
        api_data  = get_url("https://webshare.cz/api/file_info/",
                       post={'ident': re.match(cls.__pattern__, url).group('ID'),
                             'wst'  : ""})

        if re.search(r'<status>OK', api_data):
            info['status'] = 2
            info['name']   = re.search(r'<name>(.+?)<', api_data).group(1)
            info['size']   = re.search(r'<size>(.+?)<', api_data).group(1)
        elif re.search(r'<status>FATAL', api_data):
            info['status'] = 1
        else:
            info['status'] = 8
            info['error']  = _("Could not find required xml data")

        return info


    def handle_free(self, pyfile):
        wst = self.account.get_data('wst') if self.account else None

        api_data = get_url("https://webshare.cz/api/file_link/",
                           post={'ident': self.info['pattern']['ID'], 'wst': wst})

        self.log_debug("API data: " + api_data)

        m = re.search('<link>(.+)</link>', api_data)
        if m is not None:
            self.link = m.group(1)


    def handle_premium(self, pyfile):
        return self.handle_free(pyfile)
