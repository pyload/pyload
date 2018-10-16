# -*- coding: utf-8 -*-

from pyload.plugins.internal.deadhoster import DeadHoster


class UploadkingCom(DeadHoster):
    __name__ = "UploadkingCom"
    __type__ = "hoster"
    __version__ = "0.19"
    __status__ = "stable"

    __pyload_version__ = "0.5"

    __pattern__ = r"http://(?:www\.)?uploadking\.com/\w{10}"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """UploadKing.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]
