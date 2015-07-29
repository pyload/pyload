# -*- coding: utf-8 -*-

import re

from module.plugins.internal.XFSHoster import XFSHoster, create_getInfo


class XFileSharingPro(XFSHoster):
    __name__    = "XFileSharingPro"
    __type__    = "hoster"
    __version__ = "0.52"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?(?:\w+\.)*?(?P<DOMAIN>(?:[\d.]+|[\w\-^_]{3,}(?:\.[a-zA-Z]{2,}){1,2})(?:\:\d+)?)/(?:embed-)?\w{12}(?:\W|$)'

    __description__ = """XFileSharingPro dummy hoster plugin for hook"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    URL_REPLACEMENTS = [("/embed-", "/")]


    def _log(self, level, plugintype, pluginname, messages):
        return super(XFileSharingPro, self)._log(level,
                                                 plugintype,
                                                 "%s: %s" % (pluginname, self.HOSTER_NAME),
                                                 messages)


    def init(self):
        super(XFileSharingPro, self).init()

        self.__pattern__ = self.pyload.pluginManager.hosterPlugins[self.__name__]['pattern']

        self.HOSTER_DOMAIN = re.match(self.__pattern__, self.pyfile.url).group("DOMAIN").lower()
        self.HOSTER_NAME   = "".join(part.capitalize() for part in re.split(r'(\.|\d+|\-)', self.HOSTER_DOMAIN) if part != '.')

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


    def setup(self):
        self.chunk_limit     = 1
        self.resume_download = self.premium
        self.multiDL        = True


getInfo = create_getInfo(XFileSharingPro)
