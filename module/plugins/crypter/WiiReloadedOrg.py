# -*- coding: utf-8 -*-

from module.plugins.internal.DeadCrypter import DeadCrypter


class WiiReloadedOrg(DeadCrypter):
    __name__ = "WiiReloadedOrg"
    __type__ = "crypter"
    __version__ = "0.11"

    __pattern__ = r'http://(?:www\.)?wii-reloaded\.org/protect/get\.php\?i=.+'

    __description__ = """Wii-Reloaded.org decrypter plugin"""
    __authors__ = [("hzpz", None)]
