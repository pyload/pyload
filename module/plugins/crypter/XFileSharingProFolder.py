# -*- coding: utf-8 -*-

import re

from module.plugins.internal.XFSCrypter import XFSCrypter, create_getInfo


class XFileSharingProFolder(XFSCrypter):
    __name__    = "XFileSharingProFolder"
    __type__    = "crypter"
    __version__ = "0.10"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?(?:\w+\.)*?(?P<DOMAIN>(?:[\d.]+|[\w\-^_]{3,}(?:\.[a-zA-Z]{2,}){1,2})(?:\:\d+)?)/(?:user|folder)s?/\w+'
    __config__  = [("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description__ = """XFileSharingPro dummy folder decrypter plugin for hook"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    def _log(self, level, plugintype, pluginname, messages):
        return super(XFileSharingProFolder, self)._log(level, plugintype, pluginname, (self.HOSTER_NAME,) + messages)


    def init(self):
        super(XFileSharingProFolder, self).init()

        self.__pattern__ = self.pyload.pluginManager.crypterPlugins[self.__name__]['pattern']

        self.HOSTER_DOMAIN = re.match(self.__pattern__, self.pyfile.url).group("DOMAIN").lower()
        self.HOSTER_NAME   = "".join(part.capitalize() for part in re.split(r'(\.|\d+)', self.HOSTER_DOMAIN) if part != '.')

        account = self.pyload.accountManager.getAccountPlugin(self.HOSTER_NAME)

        if account and account.can_use():
            self.account = account

        elif self.account:
            self.account.HOSTER_DOMAIN = self.HOSTER_DOMAIN

        else:
            return

        self.user, data = self.account.select()
        self.req        = self.account.get_request(self.user)
        self.premium    = self.account.is_premium(self.user)


getInfo = create_getInfo(XFileSharingProFolder)
