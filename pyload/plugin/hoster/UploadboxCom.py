# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class UploadboxCom(DeadHoster):
    __name    = "Uploadbox"
    __type    = "hoster"
    __version = "0.05"

    __pattern = r'http://(?:www\.)?uploadbox\.com/files/.+'
    __config  = []

    __description = """UploadBox.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]
