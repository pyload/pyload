# -*- coding: utf-8 -*-

from module.plugins.internal.Addon import Addon, threaded


class Hook(Addon):
    __name__    = "Hook"
    __type__    = "hook"
    __version__ = "0.16"
    __status__  = "testing"

    __description__ = """Base hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("mkaay"         , "mkaay@mkaay.de"   ),
                       ("RaNaN"         , "RaNaN@pyload.org" ),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    PERIODICAL_INTERVAL = 10


    def __init__(self, *args, **kwargs):
        super(Hook, self).__init__(*args, **kwargs)
        if self.PERIODICAL_INTERVAL:
            self.start_periodical(self.PERIODICAL_INTERVAL)


    #@TODO: Remove in 0.4.10
    def _log(self, level, plugintype, pluginname, messages):
        return super(Addon, self)._log(level, plugintype, pluginname.replace("Hook", ""), messages)


    def periodical(self):
        pass
