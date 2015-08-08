# -*- coding: utf-8 -*-

from module.plugins.internal.Addon import Addon, threaded


class Hook(Addon):
    __name__    = "Hook"
    __type__    = "hook"
    __version__ = "0.13"
    __status__  = "testing"

    __config__   = []  #: [("name", "type", "desc", "default")]

    __description__ = """Base hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("mkaay"         , "mkaay@mkaay.de"   ),
                       ("RaNaN"         , "RaNaN@pyload.org" ),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    def __init__(self, core, manager):
        super(Hook, self).__init__(core, manager)
        self.init_periodical(10)


    #@TODO: Remove in 0.4.10
    def _log(self, level, plugintype, pluginname, messages):
        return super(Addon, self)._log(level, plugintype, pluginname.replace("Hook", ""), messages)
