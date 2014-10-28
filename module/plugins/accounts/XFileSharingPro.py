# -*- coding: utf-8 -*-

import re

from module.plugins.internal.XFSPAccount import XFSPAccount


class XFileSharingPro(XFSPAccount):
    __name__    = "XFileSharingPro"
    __type__    = "account"
    __version__ = "0.02"

    __description__ = """XFileSharingPro multi-purpose account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_NAME = None


    def loadAccountInfo(self, user, req):
        if self.HOSTER_NAME:
            return super(XFileSharingPro, self).loadAccountInfo(user, req)
        else:
            return {'validuntil': None, 'trafficleft': None, 'premium': None}


    def login(self, user, data, req):
        if self.HOSTER_NAME:
            return super(XFileSharingPro, self).login(user, data, req)
