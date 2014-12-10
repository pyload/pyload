# -*- coding: utf-8 -*-

from pyload.plugins.internal.XFSAccount import XFSAccount


class JunocloudMe(XFSAccount):
    __name    = "JunocloudMe"
    __type    = "account"
    __version = "0.02"

    __description = """Junocloud.me account plugin"""
    __license     = "GPLv3"
    __authors     = [("guidobelix", "guidobelix@hotmail.it")]


    HOSTER_DOMAIN = "junocloud.me"
