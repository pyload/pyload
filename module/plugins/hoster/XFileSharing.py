# -*- coding: utf-8 -*-

import re

from ..internal.XFSHoster import XFSHoster


class XFileSharing(XFSHoster):
    __name__ = "XFileSharing"
    __type__ = "hoster"
    __version__ = "0.65"
    __status__ = "testing"

    __pattern__ = r'^unmatchable$'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool",
                   "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """XFileSharing dummy hoster plugin for hook"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    URL_REPLACEMENTS = [("/embed-", "/")]

    def _log(self, level, plugintype, pluginname, messages):
        messages = (self.PLUGIN_NAME,) + messages
        return XFSHoster._log(
            self, level, plugintype, pluginname, messages)

    def init(self):
        self.__pattern__ = self.pyload.pluginManager.hosterPlugins[
            self.classname]['pattern']

        self.PLUGIN_DOMAIN = re.match(
            self.__pattern__,
            self.pyfile.url).group("DOMAIN").lower()
        self.PLUGIN_NAME = "".join(
            part.capitalize() for part in re.split(
                r'\.|\d+|-', self.PLUGIN_DOMAIN) if part != '.')

    def setup(self):
        self.chunk_limit = -1 if self.premium else 1
        self.multiDL = True
        self.resume_download = self.premium

    #@TODO: Recheck in 0.4.10
    def setup_base(self):
        XFSHoster.setup_base(self)

        if self.account:
            self.req = self.pyload.requestFactory.getRequest(
                self.PLUGIN_NAME, self.account.user)
            # @NOTE: Don't call get_info here to reduce overhead
            self.premium = self.account.info['data']['premium']
        else:
            self.req = self.pyload.requestFactory.getRequest(self.classname)
            self.premium = False

    #@TODO: Recheck in 0.4.10
    def load_account(self):
        class_name = self.classname
        self.__class__.__name__ = str(self.PLUGIN_NAME)
        XFSHoster.load_account(self)
        self.__class__.__name__ = class_name
