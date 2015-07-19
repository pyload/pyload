# -*- coding: utf-8 -*-

from module.plugins.internal.Addon import Addon


class Hook(Addon):
    __name__    = "Hook"
    __type__    = "hook"
    __version__ = "0.10"
    __status__  = "stable"

    __config__   = []  #: [("name", "type", "desc", "default")]

    __description__ = """Base hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("mkaay"         , "mkaay@mkaay.de"   ),
                       ("RaNaN"         , "RaNaN@pyload.org" ),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    def __init__(self, core, manager):
        super(Hook, self).__init__(core, manager)
        self.init_periodical(10)
