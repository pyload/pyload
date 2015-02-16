# -*- coding: utf-8 -*-

from urllib import unquote

from pyload.plugin.internal.MultiHoster import MultiHoster


class RehostTo(MultiHoster):
    __name    = "RehostTo"
    __type    = "hoster"
    __version = "0.21"

    __pattern = r'https?://.*rehost\.to\..+'

    __description = """Rehost.com multi-hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("RaNaN", "RaNaN@pyload.org")]


    def handlePremium(self, pyfile):
        self.download("http://rehost.to/process_download.php",
                      get={'user': "cookie",
                           'pass': self.account.getAccountInfo(self.user)['session'],
                           'dl'  : pyfile.url},
                      disposition=True)
