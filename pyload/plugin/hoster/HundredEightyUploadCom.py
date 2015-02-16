# -*- coding: utf-8 -*-

from pyload.plugin.internal.XFSHoster import XFSHoster


class HundredEightyUploadCom(XFSHoster):
    __name    = "HundredEightyUploadCom"
    __type    = "hoster"
    __version = "0.04"

    __pattern = r'http://(?:www\.)?180upload\.com/\w{12}'

    __description = """180upload.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("stickell", "l.stickell@yahoo.it")]
