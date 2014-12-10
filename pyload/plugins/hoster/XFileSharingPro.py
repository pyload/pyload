# -*- coding: utf-8 -*-

import re

from pyload.plugins.internal.XFSHoster import XFSHoster, create_getInfo


class XFileSharingPro(XFSHoster):
    __name    = "XFileSharingPro"
    __type    = "hoster"
    __version = "0.43"

    __pattern = r'^unmatchable$'

    __description = """XFileSharingPro dummy hoster plugin for hook"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


    URL_REPLACEMENTS = [("/embed-", "/")]


    def _log(self, type, args):
        msg = " | ".join([str(a).strip() for a in args if a])
        logger = getattr(self.log, type)
        logger("%s: %s: %s" % (self.__name, self.HOSTER_NAME, msg or _("%s MARK" % type.upper())))


    def init(self):
        super(XFileSharingPro, self).init()

        self.__pattern = self.core.pluginManager.hosterPlugins[self.__name]['pattern']

        self.HOSTER_DOMAIN = re.match(self.__pattern, self.pyfile.url).group(1).lower()
        self.HOSTER_NAME   = "".join([str.capitalize() for str in self.HOSTER_DOMAIN.split('.')])

        account = self.core.accountManager.getAccountPlugin(self.HOSTER_NAME)

        if account and account.canUse():
            self.account = account
        elif self.account:
            self.account.HOSTER_DOMAIN = self.HOSTER_DOMAIN
        else:
            return

        self.user, data = self.account.selectAccount()
        self.req = self.account.getAccountRequest(self.user)
        self.premium = self.account.isPremium(self.user)


    def setup(self):
        self.chunkLimit = 1
        self.resumeDownload = self.premium
        self.multiDL = True


getInfo = create_getInfo(XFileSharingPro)
