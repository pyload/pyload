# -*- coding: utf-8 -*-

from module.plugins.internal.XFSPAccount import XFSPAccount


class JunocloudMe(XFSPAccount):
    __name__ = "JunocloudMe"
    __type__ = "account"
    __version__ = "0.01"

    __description__ = """Junocloud.me account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("guidobelix", "guidobelix@hotmail.it")]


    HOSTER_NAME = "junocloud.me"
