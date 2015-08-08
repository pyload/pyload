# -*- coding: utf-8 -*-

from module.plugins.internal.XFSAccount import XFSAccount


class RapidfileshareNet(XFSAccount):
    __name__    = "RapidfileshareNet"
    __type__    = "account"
    __version__ = "0.06"
    __status__  = "testing"

    __description__ = """Rapidfileshare.net account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("guidobelix", "guidobelix@hotmail.it")]


    HOSTER_DOMAIN = "rapidfileshare.net"

    TRAFFIC_LEFT_PATTERN = r'>Traffic available today:</TD><TD><label for="name">\s*(?P<S>[\d.,]+)\s*(?:(?P<U>[\w^_]+))?'
