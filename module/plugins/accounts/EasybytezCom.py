# -*- coding: utf-8 -*-

import re

from module.plugins.internal.XFSAccount import XFSAccount


class EasybytezCom(XFSAccount):
    __name__    = "EasybytezCom"
    __type__    = "account"
    __version__ = "0.12"

    __description__ = """EasyBytez.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("guidobelix", "guidobelix@hotmail.it")]


    HOSTER_DOMAIN = "easybytez.com"
