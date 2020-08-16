# -*- coding: utf-8 -*-

from ..base.dead_decrypter import DeadDecrypter


class WiiReloadedOrg(DeadDecrypter):
    __name__ = "WiiReloadedOrg"
    __type__ = "decrypter"
    __version__ = "0.16"
    __status__ = "stable"

    __pattern__ = r"http://(?:www\.)?wii-reloaded\.org/protect/get\.php\?i=.+"
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """Wii-Reloaded.org decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("hzpz", None)]
