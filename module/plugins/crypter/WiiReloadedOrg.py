# -*- coding: utf-8 -*-

from module.plugins.internal.DeadCrypter import DeadCrypter


class WiiReloadedOrg(DeadCrypter):
    __name__ = "WiiReloadedOrg"
    __type__ = "crypter"
    __pattern__ = r"http://www\.wii-reloaded\.org/protect/get\.php\?i=.+"
    __version__ = "0.11"
    __description__ = """Wii-Reloaded.org Crypter Plugin"""
    __author_name__ = ("hzpz")
    __author_mail__ = ("none")
