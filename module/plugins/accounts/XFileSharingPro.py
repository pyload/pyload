# -*- coding: utf-8 -*-

from module.plugins.internal.XFSAccount import XFSAccount


class XFileSharing(XFSAccount):
    __name__    = "XFileSharing"
    __type__    = "account"
    __version__ = "0.11"
    __status__  = "testing"

    __description__ = """XFileSharing multi-purpose account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    PLUGIN_DOMAIN = None


    def signin(self, user, password, data):
        try:
            return super(XFileSharing, self).signin(user, password, data)

        except Fail:
            self.PLUGIN_URL = self.PLUGIN_URL.replace("www.", "")
            return super(XFileSharing, self).signin(user, password, data)
