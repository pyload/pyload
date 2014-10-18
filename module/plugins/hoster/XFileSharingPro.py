# -*- coding: utf-8 -*-

import re

from module.plugins.internal.XFSPHoster import XFSPHoster, create_getInfo


class XFileSharingPro(XFSPHoster):
    __name__ = "XFileSharingPro"
    __type__ = "hoster"
    __version__ = "0.39"

    __pattern__ = r'^unmatchable$'

    __description__ = """XFileSharingPro dummy hoster plugin for hook"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]


    FILE_URL_REPLACEMENTS = [(r'/embed-(\w{12}).*', r'/\1')]  #: support embedded files


    def init(self):
        self.__pattern__ = self.core.pluginManager.hosterPlugins[self.__name__]['pattern']
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


    def setup(self):
        self.chunkLimit = 1
        self.resumeDownload = self.premium
        self.multiDL = True


getInfo = create_getInfo(XFileSharingPro)
