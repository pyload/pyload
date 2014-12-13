# -*- coding: utf-8 -*-

from pyload.plugin.internal.XFSAccount import XFSAccount


class RapidfileshareNet(XFSAccount):
    __name    = "RapidfileshareNet"
    __type    = "account"
    __version = "0.05"

    __description = """Rapidfileshare.net account plugin"""
    __license     = "GPLv3"
    __authors     = [("guidobelix", "guidobelix@hotmail.it")]


    HOSTER_DOMAIN = "rapidfileshare.net"

    TRAFFIC_LEFT_PATTERN = r'>Traffic available today:</TD><TD><label for="name">\s*(?P<S>[\d.,]+)\s*(?:(?P<U>[\w^_]+))?'
