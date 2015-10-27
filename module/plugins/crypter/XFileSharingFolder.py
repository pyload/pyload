# -*- coding: utf-8 -*-

import re

from module.plugins.internal.XFSCrypter import XFSCrypter, create_getInfo


class XFileSharingFolder(XFSCrypter):
    __name__    = "XFileSharingFolder"
    __type__    = "crypter"
    __version__ = "0.23"
    __status__  = "testing"

    __pattern__ = r'^unmatchable$'
    __config__  = [("activated"            , "bool", "Activated"                                        , True),
                   ("use_premium"          , "bool", "Use premium account if available"                 , True),
                   ("use_subfolder"        , "bool", "Save package to subfolder"                        , True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package"              , True),
                   ("max_wait"             , "int" , "Reconnect if waiting time is greater than minutes", 10  )]

    __description__ = """XFileSharing dummy folder decrypter plugin for hook"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    def _log(self, level, plugintype, pluginname, messages):
        messages = (self.PLUGIN_NAME,) + messages
        return super(XFileSharingFolder, self)._log(level, plugintype, pluginname, messages)


    def init(self):
        self.__pattern__ = self.pyload.pluginManager.crypterPlugins[self.classname]['pattern']

        self.PLUGIN_DOMAIN = re.match(self.__pattern__, self.pyfile.url).group("DOMAIN").lower()
        self.PLUGIN_NAME   = "".join(part.capitalize() for part in re.split(r'\.|\d+|-', self.PLUGIN_DOMAIN) if part != '.')


    #@TODO: Recheck in 0.4.10
    def setup_base(self):
        if self.account:
            self.req     = self.pyload.requestFactory.getRequest(self.PLUGIN_NAME, self.account.user)
            self.premium = self.account.info['data']['premium']  #@NOTE: Avoid one unnecessary get_info call by `self.account.premium` here
        else:
            self.req     = self.pyload.requestFactory.getRequest(self.classname)
            self.premium = False

        super(XFileSharingFolder, self).setup_base()


    #@TODO: Recheck in 0.4.10
    def load_account(self):
        class_name = self.classname
        self.__class__.__name__ = str(self.PLUGIN_NAME)
        super(XFileSharingFolder, self).load_account()
        self.__class__.__name__ = class_name


getInfo = create_getInfo(XFileSharingFolder)
