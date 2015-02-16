# -*- coding: utf-8 -*-

from pyload.plugin.internal.XFSCrypter import XFSCrypter


class EasybytezCom(XFSCrypter):
    __name    = "EasybytezCom"
    __type    = "crypter"
    __version = "0.10"

    __pattern = r'http://(?:www\.)?easybytez\.com/users/\d+/\d+'
    __config  = [("use_subfolder", "bool", "Save package to subfolder", True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description = """Easybytez.com folder decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("stickell", "l.stickell@yahoo.it")]


    LOGIN_ACCOUNT = True
