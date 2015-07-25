# -*- coding: utf-8 -*-

from module.plugins.internal.XFSAccount import XFSAccount


class XFileSharingPro(XFSAccount):
    __name__    = "XFileSharingPro"
    __type__    = "account"
    __version__ = "0.07"
    __status__  = "testing"

    __description__ = """XFileSharingPro multi-purpose account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_DOMAIN = None


    def init(self):
        if self.HOSTER_DOMAIN:
            return super(XFileSharingPro, self).init()


    def login(self, user, password, data, req):
        if self.HOSTER_DOMAIN:
            try:
                return super(XFileSharingPro, self).login(user, data, req)
            except Exception:
                self.HOSTER_URL = self.HOSTER_URL.replace("www.", "")
                return super(XFileSharingPro, self).login(user, data, req)
