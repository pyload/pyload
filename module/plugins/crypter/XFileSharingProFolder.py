# -*- coding: utf-8 -*-

import re

from module.plugins.internal.XFSPCrypter import XFSPCrypter


class XFileSharingProFolder(XFSPCrypter):
    __name__    = "XFileSharingProFolder"
    __type__    = "crypter"
    __version__ = "0.02"

    __pattern__ = r'^unmatchable$'
    __config__  = [("use_subfolder", "bool", "Save package to subfolder", True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description__ = """XFileSharingPro dummy folder decrypter plugin for hook"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    def init(self):
        self.__pattern__ = self.core.pluginManager.crypterPlugins[self.__name__]['pattern']
        self.HOSTER_NAME = re.match(self.__pattern__, self.pyfile.url).group(1).lower()

        account_name = "".join([str.capitalize() for str in self.HOSTER_NAME.split('.')])
        account = self.core.accountManager.getAccountPlugin(account_name)

        if account and account.canUse():
            self.user, data = account.selectAccount()
            self.req = account.getAccountRequest(self.user)
            self.premium = account.isPremium(self.user)

            self.account = account
        else:
            self.account.HOSTER_NAME = self.HOSTER_NAME
