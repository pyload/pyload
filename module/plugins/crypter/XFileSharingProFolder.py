# -*- coding: utf-8 -*-

import re

from module.plugins.internal.XFSCrypter import XFSCrypter, create_getInfo


class XFileSharingProFolder(XFSCrypter):
    __name__    = "XFileSharingProFolder"
    __type__    = "crypter"
    __version__ = "0.08"

    __pattern__ = r'https?://(?:www\.)?(?:\w+\.)*?(?P<DOMAIN>(?:[\d.]+|[\w\-^_]{3,}(?:\.[a-zA-Z]{2,}){1,2})(?:\:\d+)?)/(?:user|folder)s?/\w+'
    __config__  = [("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description__ = """XFileSharingPro dummy folder decrypter plugin for hook"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    def _log(self, type, args):
        return super(XFileSharingProFolder, self)._log(type, (self.HOSTER_NAME,) + args)


    def init(self):
        super(XFileSharingProFolder, self).init()

        self.__pattern__ = self.core.pluginManager.crypterPlugins[self.__name__]['pattern']

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


getInfo = create_getInfo(XFileSharingProFolder)
