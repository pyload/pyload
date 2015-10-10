# -*- coding: utf-8 -*-

from module.plugins.internal.DeadCrypter import DeadCrypter, create_getInfo


class WiiReloadedOrg(DeadCrypter):
    __name__    = "WiiReloadedOrg"
    __type__    = "crypter"
    __version__ = "0.12"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?wii-reloaded\.org/protect/get\.php\?i=.+'
    __config__  = []  #@TODO: Remove in 0.4.10

    __description__ = """Wii-Reloaded.org decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("hzpz", None)]


getInfo = create_getInfo(WiiReloadedOrg)
