# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class UploadkingCom(DeadHoster):
    __name__    = "UploadkingCom"
    __type__    = "hoster"
    __version__ = "0.14"

    __pattern__ = r'http://(?:www\.)?uploadking\.com/\w{10}'
    __config__  = []

    __description__ = """UploadKing.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]
