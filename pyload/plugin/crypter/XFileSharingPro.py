# -*- coding: utf-8 -*-

import re

from pyload.plugin.internal.XFSCrypter import XFSCrypter


class XFileSharingPro(XFSCrypter):
    __name    = "XFileSharingPro"
    __type    = "crypter"
    __version = "0.05"

    __pattern = r'^unmatchable$'
    __config  = [("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                 ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description = """XFileSharingPro dummy folder decrypter plugin for hook"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


    def _log(self, type, args):
        msg = " | ".join(str(a).strip() for a in args if a)
        logger = getattr(self.log, type)
        logger("%s: %s: %s" % (self.__class__.__name__, self.HOSTER_NAME, msg or _("%s MARK" % type.upper())))


    def init(self):
        super(XFileSharingPro, self).init()

        self.__pattern = self.core.pluginManager.crypterPlugins[self.__class__.__name__]['pattern']

        self.HOSTER_DOMAIN = re.match(self.__pattern, self.pyfile.url).group("DOMAIN").lower()
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
