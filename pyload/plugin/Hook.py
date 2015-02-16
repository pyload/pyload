# -*- coding: utf-8 -*-

from pyload.plugin.Addon import Addon, threaded


class Hook(Addon):
    __name    = "Hook"
    __type    = "hook"
    __version = "0.03"

    __config = []  #: [("name", "type", "desc", "default")]

    __description = """Base hook plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]
