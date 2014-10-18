# -*- coding: utf-8 -*-

from module.plugins.internal.XFSPCrypter import XFSPCrypter


class EasybytezComFolder(XFSPCrypter):
    __name__ = "EasybytezComFolder"
    __type__ = "crypter"
    __version__ = "0.09"

    __pattern__ = r'http://(?:www\.)?easybytez\.com/users/(?P<ID>\d+/\d+)'

    __description__ = """Easybytez.com folder decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("stickell", "l.stickell@yahoo.it")]


    HOSTER_NAME = "easybytez.com"

    LOGIN_ACCOUNT = True
