# -*- coding: utf-8 -*-

from urllib import unquote

from module.plugins.internal.MultiHoster import MultiHoster, create_getInfo


class RehostTo(MultiHoster):
    __name__    = "RehostTo"
    __type__    = "hoster"
    __version__ = "0.21"

    __pattern__ = r'https?://.*rehost\.to\..+'

    __description__ = """Rehost.com multi-hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN", "RaNaN@pyload.org")]


    def handlePremium(self, pyfile):
        self.download("http://rehost.to/process_download.php",
                      get={'user': "cookie",
                           'pass': self.account.getAccountInfo(self.user)['session'],
                           'dl'  : pyfile.url},
                      disposition=True)


getInfo = create_getInfo(RehostTo)
