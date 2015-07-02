# -*- coding: utf-8 -*-

import re

from module.plugins.internal.XFSHoster import XFSHoster, create_getInfo


class XFileSharingPro(XFSHoster):
    __name__    = "XFileSharingPro"
    __type__    = "hoster"
    __version__ = "0.48"

    __pattern__ = r'https?://(?:www\.)?(?:\w+\.)*?(?P<DOMAIN>(?:[\d.]+|[\w\-^_]{3,}(?:\.[a-zA-Z]{2,}){1,2})(?:\:\d+)?)/(?:embed-)?\w{12}(?:\W|$)'

    __description__ = """XFileSharingPro dummy hoster plugin for hook"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    URL_REPLACEMENTS = [("/embed-(\w+)-?[0-9x]*", "/\\1")]


    def _log(self, type, args):
        return super(XFileSharingPro, self)._log(type, (self.HOSTER_NAME,) + args)


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
