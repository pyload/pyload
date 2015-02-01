# -*- coding: utf-8 -*-

import re

from module.plugins.internal.XFSCrypter import XFSCrypter, create_getInfo


class XFileSharingProFolder(XFSCrypter):
    __name__    = "XFileSharingProFolder"
    __type__    = "crypter"
    __version__ = "0.04"

    __pattern__ = r'^unmatchable$'
    __config__  = [("use_subfolder", "bool", "Save package to subfolder", True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description__ = """XFileSharingPro dummy folder decrypter plugin for hook"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    def _log(self, type, args):
        msg = " | ".join(str(a).strip() for a in args if a)
        logger = getattr(self.log, type)
        logger("%s: %s: %s" % (self.__name__, self.HOSTER_NAME, msg or _("%s MARK" % type.upper())))


    def init(self):
        super(XFileSharingProFolder, self).init()

        self.__pattern__ = self.core.pluginManager.crypterPlugins[self.__name__]['pattern']

        self.HOSTER_DOMAIN = re.match(self.__pattern__, self.pyfile.url).group("DOMAIN").lower()
        self.HOSTER_NAME   = "".join(part.capitalize() for part in re.split(r'(\.|\d+)', self.HOSTER_DOMAIN) if part != '.')

        if self.HOSTER_NAME[0].isdigit():
            self.HOSTER_NAME = 'X' + self.HOSTER_NAME

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


getInfo = create_getInfo(XFileSharingProFolder)
