# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class UploadhereCom(DeadHoster):
    __name    = "UploadhereCom"
    __type    = "hoster"
    __version = "0.12"

    __pattern = r'http://(?:www\.)?uploadhere\.com/\w{10}'
    __config  = []

    __description = """Uploadhere.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]
