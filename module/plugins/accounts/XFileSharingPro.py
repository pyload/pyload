# -*- coding: utf-8 -*-

from module.plugins.internal.XFSAccount import XFSAccount


class XFileSharingPro(XFSAccount):
    __name__    = "XFileSharingPro"
    __type__    = "account"
    __version__ = "0.09"
    __status__  = "testing"

    __description__ = """XFileSharingPro multi-purpose account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_DOMAIN = None


    def login(self, user, password, data, req):
        try:
            return super(XFileSharingPro, self).login(user, data, req)

        except Fail:
            self.HOSTER_URL = self.HOSTER_URL.replace("www.", "")
            return super(XFileSharingPro, self).login(user, data, req)
