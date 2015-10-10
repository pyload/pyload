# -*- coding: utf-8 -*-

from module.plugins.internal.XFSAccount import XFSAccount


class XFileSharingPro(XFSAccount):
    __name__    = "XFileSharingPro"
    __type__    = "account"
    __version__ = "0.10"
    __status__  = "testing"

    __description__ = """XFileSharingPro multi-purpose account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    PLUGIN_DOMAIN = None


    def signin(self, user, password, data):
        try:
            return super(XFileSharingPro, self).signin(user, password, data)

        except Fail:
            self.PLUGIN_URL = self.PLUGIN_URL.replace("www.", "")
            return super(XFileSharingPro, self).signin(user, password, data)
