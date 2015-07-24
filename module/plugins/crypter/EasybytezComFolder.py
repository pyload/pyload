# -*- coding: utf-8 -*-

from module.plugins.internal.XFSCrypter import XFSCrypter, create_getInfo


class EasybytezComFolder(XFSCrypter):
    __name__    = "EasybytezComFolder"
    __type__    = "crypter"
    __version__ = "0.11"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?easybytez\.com/users/\d+/\d+'
    __config__  = [("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description__ = """Easybytez.com folder decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it")]


    LOGIN_ACCOUNT = True


getInfo = create_getInfo(EasybytezComFolder)
