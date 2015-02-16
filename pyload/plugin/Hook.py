# -*- coding: utf-8 -*-

from pyload.plugin.Addon import Addon, threaded


class Hook(Addon):
    __name__    = "Hook"
    __type__    = "hook"
    __version__ = "0.03"

    __config__ = []  #: [("name", "type", "desc", "default")]

    __description__ = """Base hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]
