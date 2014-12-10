# -*- coding: utf-8 -*-

import re

from pyload.plugins.internal.XFSAccount import XFSAccount


class EasybytezCom(XFSAccount):
    __name    = "EasybytezCom"
    __type    = "account"
    __version = "0.12"

    __description = """EasyBytez.com account plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("guidobelix", "guidobelix@hotmail.it")]


    HOSTER_DOMAIN = "easybytez.com"
