# -*- coding: utf-8 -*-

from module.plugins.internal.XFSAccount import XFSAccount


class JunocloudMe(XFSAccount):
    __name__    = "JunocloudMe"
    __type__    = "account"
    __version__ = "0.03"
    __status__  = "testing"

    __description__ = """Junocloud.me account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("guidobelix", "guidobelix@hotmail.it")]


    HOSTER_DOMAIN = "junocloud.me"
