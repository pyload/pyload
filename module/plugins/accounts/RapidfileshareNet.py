# -*- coding: utf-8 -*-

from module.plugins.internal.XFSPAccount import XFSPAccount


class RapidfileshareNet(XFSPAccount):
    __name__ = "RapidfileshareNet"
    __type__ = "account"
    __version__ = "0.04"

    __description__ = """Rapidfileshare.net account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("guidobelix", "guidobelix@hotmail.it")]


    HOSTER_URL = "http://www.rapidfileshare.net/"

    TRAFFIC_LEFT_PATTERN = r'>Traffic available today:</TD><TD><label for="name">\s*(?P<S>[\d.,]+)\s*(?:(?P<U>[\w^_]+)\s*)?</label></TD></TR>'
