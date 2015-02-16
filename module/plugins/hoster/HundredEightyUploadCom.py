# -*- coding: utf-8 -*-

from pyload.plugin.internal.XFSHoster import XFSHoster, create_getInfo


class HundredEightyUploadCom(XFSHoster):
    __name__    = "HundredEightyUploadCom"
    __type__    = "hoster"
    __version__ = "0.04"

    __pattern__ = r'http://(?:www\.)?180upload\.com/\w{12}'

    __description__ = """180upload.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it")]



getInfo = create_getInfo(HundredEightyUploadCom)
