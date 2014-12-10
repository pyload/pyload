# -*- coding: utf-8 -*-

from pyload.plugins.internal.XFSAccount import XFSAccount


class XFileSharingPro(XFSAccount):
    __name    = "XFileSharingPro"
    __type    = "account"
    __version = "0.05"

    __description = """XFileSharingPro multi-purpose account plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_DOMAIN = None


    def init(self):
        if self.HOSTER_DOMAIN:
            return super(XFileSharingPro, self).init()


    def loadAccountInfo(self, user, req):
        return super(XFileSharingPro if self.HOSTER_DOMAIN else XFSAccount, self).loadAccountInfo(user, req)


    def login(self, user, data, req):
        if self.HOSTER_DOMAIN:
            return super(XFileSharingPro, self).login(user, data, req)
