# -*- coding: utf-8 -*-

from pyload.plugins.internal.DeadCrypter import DeadCrypter, create_getInfo


class WiiReloadedOrg(DeadCrypter):
    __name    = "WiiReloadedOrg"
    __type    = "crypter"
    __version = "0.11"

    __pattern = r'http://(?:www\.)?wii-reloaded\.org/protect/get\.php\?i=.+'
    __config  = []

    __description = """Wii-Reloaded.org decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("hzpz", "")]


getInfo = create_getInfo(WiiReloadedOrg)
