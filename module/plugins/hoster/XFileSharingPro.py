# -*- coding: utf-8 -*-

import re

from module.plugins.internal.XFSHoster import XFSHoster, create_getInfo


class XFileSharingPro(XFSHoster):
    __name__    = "XFileSharingPro"
    __type__    = "hoster"
    __version__ = "0.45"

    __pattern__ = r'^unmatchable$'

    __description__ = """XFileSharingPro dummy hoster plugin for hook"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    URL_REPLACEMENTS = [("/embed-", "/")]


    def _log(self, type, args):
        msg = " | ".join(str(a).strip() for a in args if a)
        logger = getattr(self.log, type)
        logger("%s: %s: %s" % (self.__name__, self.HOSTER_NAME, msg or _("%s MARK" % type.upper())))


    def init(self):
        super(XFileSharingPro, self).init()

        self.__pattern__ = self.core.pluginManager.hosterPlugins[self.__name__]['pattern']

        self.HOSTER_DOMAIN = re.match(self.__pattern__, self.pyfile.url).group("DOMAIN").lower()
        self.HOSTER_NAME   = "".join(part.capitalize() for part in re.split(r'(\.|\d+)', self.HOSTER_DOMAIN) if part != '.')

        account = self.core.accountManager.getAccountPlugin(self.HOSTER_NAME)

        if account and account.canUse():
            self.account = account

        elif self.account:
            self.account.HOSTER_DOMAIN = self.HOSTER_DOMAIN

        else:
            return

        self.user, data = self.account.selectAccount()
        self.req        = self.account.getAccountRequest(self.user)
        self.premium    = self.account.isPremium(self.user)


    def setup(self):
        self.chunkLimit     = 1
        self.resumeDownload = self.premium
        self.multiDL        = True


getInfo = create_getInfo(XFileSharingPro)
