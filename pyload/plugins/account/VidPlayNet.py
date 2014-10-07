# -*- coding: utf-8 -*-

from pyload.plugins.internal.XFSPAccount import XFSPAccount


class VidPlayNet(XFSPAccount):
    __name__ = "VidPlayNet"
    __type__ = "account"
    __version__ = "0.01"

    __description__ = """VidPlay.net account plugin"""
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_URL = "http://www.vidplay.net/"
