# -*- coding: utf-8 -*-

import re

from ..internal.XFSCrypter import XFSCrypter


class XFileSharingFolder(XFSCrypter):
    __name__ = "XFileSharingFolder"
    __type__ = "crypter"
    __version__ = "0.25"
    __status__ = "testing"

    __pattern__ = r'^unmatchable$'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("folder_per_package", "Default;Yes;No",
                   "Create folder for each package", "Default"),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """XFileSharing dummy folder decrypter plugin for hook"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    def _log(self, level, plugintype, pluginname, messages):
        messages = (self.PLUGIN_NAME,) + messages
        return XFSCrypter._log(self, level, plugintype, pluginname, messages)

    def init(self):
        self.__pattern__ = self.pyload.pluginManager.crypterPlugins[
            self.classname]['pattern']

        self.PLUGIN_DOMAIN = re.match(
            self.__pattern__,
            self.pyfile.url).group("DOMAIN").lower()
        self.PLUGIN_NAME = "".join(
            part.capitalize() for part in re.split(
                r'\.|\d+|-', self.PLUGIN_DOMAIN) if part != '.')

    #@TODO: Recheck in 0.4.10
    def setup_base(self):
        XFSCrypter.setup_base(self)

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
        XFSCrypter.load_account(self)
        self.__class__.__name__ = class_name
