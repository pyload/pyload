# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class UploadkingCom(DeadHoster):
    __name    = "UploadkingCom"
    __type    = "hoster"
    __version = "0.14"

    __pattern = r'http://(?:www\.)?uploadking\.com/\w{10}'

    __description = """UploadKing.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]
