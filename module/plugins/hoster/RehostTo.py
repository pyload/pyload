# -*- coding: utf-8 -*-

import urllib

from module.plugins.internal.MultiHoster import MultiHoster, create_getInfo


class RehostTo(MultiHoster):
    __name__    = "RehostTo"
    __type__    = "hoster"
    __version__ = "0.23"
    __status__  = "testing"

    __pattern__ = r'https?://.*rehost\.to\..+'
    __config__  = [("use_premium" , "bool", "Use premium account if available"    , True),
                   ("revertfailed", "bool", "Revert to standard download if fails", True)]

    __description__ = """Rehost.com multi-hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN", "RaNaN@pyload.org")]


    def handle_premium(self, pyfile):
        self.download("http://rehost.to/process_download.php",
                      get={'user': "cookie",
                           'pass': self.account.get_data(self.user)['session'],
                           'dl'  : pyfile.url},
                      disposition=True)


getInfo = create_getInfo(RehostTo)
