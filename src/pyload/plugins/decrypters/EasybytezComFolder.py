# -*- coding: utf-8 -*-

from ..base.xfs_decrypter import XFSDecrypter


class EasybytezComFolder(XFSDecrypter):
    __name__ = "EasybytezComFolder"
    __type__ = "decrypter"
    __version__ = "0.17"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?easybytez\.com/users/\d+/\d+"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        (
            "folder_per_package",
            "Default;Yes;No",
            "Create folder for each package",
            "Default",
        ),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Easybytez.com folder decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("stickell", "l.stickell@yahoo.it")]

    PLUGIN_DOMAIN = "easybytez.com"

    LOGIN_ACCOUNT = True
