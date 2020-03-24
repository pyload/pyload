# -*- coding: utf-8 -*-

import pycurl

from ..internal.MultiHoster import MultiHoster


class GetTwentyFourOrg(MultiHoster):
    __name__ = 'GetTwentyFourOrg'
    __type__ = 'hoster'
    __version__ = '0.03'
    __status__ = 'testing'

    __pattern__ = r'^unmatchable$'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool", "Fallback to free download if premium fails", False),
                  ("chk_filesize", "bool", "Check file size", False),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
                  ("revert_failed", "bool", "Revert to standard download if fails", True)]

    __description__ = 'GeT24.org multi-hoster plugin'
    __license__ = 'GPLv3'
    __authors__ = ['get24', 'contact@get24.org']

    API_URL = 'https://get24.org/api'

    def handle_premium(self, pyfile):
        self.req.http.c.setopt(  # TODO?: move to new method - api request
            pycurl.USERAGENT, "pyLoad/{}".format(self.pyload.version).encode()
        )
        post = {'email': self.account.user,
                'passwd_sha256': self.account.info['data']['passwd_sha256'],
                'url': pyfile.url}
        self.download('%s/download' % self.API_URL, post=post)
