# -*- coding: utf-8 -*-

import re

from module.plugins.internal.XFSHoster import XFSHoster, create_getInfo


class XFileSharingPro(XFSHoster):
    __name__    = "XFileSharingPro"
    __type__    = "hoster"
    __version__ = "0.54"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?(?:\w+\.)*?(?P<DOMAIN>(?:[\d.]+|[\w\-^_]{3,}(?:\.[a-zA-Z]{2,}){1,2})(?:\:\d+)?)/(?:embed-)?\w{12}(?:\W|$)'
    __config__  = [("activated", "bool", "Activated", True)]

    __description__ = """XFileSharingPro dummy hoster plugin for hook"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    URL_REPLACEMENTS = [("/embed-", "/")]


    def _log(self, level, plugintype, pluginname, messages):
        return super(XFileSharingPro, self)._log(level,
                                                 plugintype,
                                                 "%s: %s" % (pluginname, self.PLUGIN_NAME),
                                                 messages)


    def init(self):
        self.__pattern__ = self.pyload.pluginManager.hosterPlugins[self.classname]['pattern']

        self.PLUGIN_DOMAIN = re.match(self.__pattern__, self.pyfile.url).group("DOMAIN").lower()
        self.PLUGIN_NAME   = "".join(part.capitalize() for part in re.split(r'(\.|\d+|-)', self.PLUGIN_DOMAIN) if part != '.')


    def _setup(self):
        account_name     = self.classname if self.account.PLUGIN_DOMAIN is None else self.PLUGIN_NAME
        self.chunk_limit = 1
        self.multiDL     = True

        if self.account:
            self.req             = self.pyload.requestFactory.getRequest(accountname, self.account.user)
            self.premium         = self.account.premium
            self.resume_download = self.premium
        else:
            self.req             = self.pyload.requestFactory.getRequest(account_name)
            self.premium         = False
            self.resume_download = False


    def load_account(self):
        if self.req:
            self.req.close()

        if not self.account:
            self.account = self.pyload.accountManager.getAccountPlugin(self.PLUGIN_NAME)

        if not self.account:
            self.account = self.pyload.accountManager.getAccountPlugin(self.classname)

        if self.account:
            if not self.account.PLUGIN_DOMAIN:
                self.account.PLUGIN_DOMAIN = self.PLUGIN_DOMAIN

            if not self.account.user:  #@TODO: Move to `Account` in 0.4.10
                self.account.user = self.account.select()[0]

            if not self.account.logged:
                self.account = False


getInfo = create_getInfo(XFileSharingPro)
