# -*- coding: utf-8 -*-

from module.plugins.internal.XFSPAccount import XFSPAccount


class XFileSharingPro(XFSPAccount):
    __name__    = "XFileSharingPro"
    __type__    = "account"
    __version__ = "0.04"

    __description__ = """XFileSharingPro multi-purpose account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_NAME = None


    def init(self):
        if self.HOSTER_NAME:
            return super(XFileSharingPro, self).init()


    def loadAccountInfo(self, user, req):
        return super(XFileSharingPro if self.HOSTER_NAME else XFSPAccount, self).loadAccountInfo(user, req)


    def login(self, user, data, req):
        if self.HOSTER_NAME:
            return super(XFileSharingPro, self).login(user, data, req)
