# -*- coding: utf-8 -*-

import re

from module.plugins.internal.MultiHoster import MultiHoster


class EasybytezCom(MultiHoster):
    __name__ = "EasybytezCom"
    __type__ = "hook"
    __version__ = "0.03"

    __config__ = [("activated", "bool", "Activated", False),
                  ("hosterListMode", "all;listed;unlisted", "Use for hosters (if supported)", "all"),
                  ("hosterList", "str", "Hoster list (comma separated)", "")]

    __description__ = """EasyBytez.com hook plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"


    def getHoster(self):
        self.account = self.core.accountManager.getAccountPlugin(self.__name__)
        user = self.account.selectAccount()[0]

        try:
            req = self.account.getAccountRequest(user)
            page = req.load("http://www.easybytez.com")

            m = re.search(r'</textarea>\s*Supported sites:(.*)', page)
            return m.group(1).split(',')
        except Exception, e:
            self.logDebug(e)
            self.logWarning("Unable to load supported hoster list, using last known")
            return ["bitshare.com", "crocko.com", "ddlstorage.com", "depositfiles.com", "extabit.com", "hotfile.com",
                    "mediafire.com", "netload.in", "rapidgator.net", "rapidshare.com", "uploading.com", "uload.to",
                    "uploaded.to"]
