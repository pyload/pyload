# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class Share76Com(DeadHoster):
    __name    = "Share76Com"
    __type    = "hoster"
    __version = "0.04"

    __pattern = r'http://(?:www\.)?share76\.com/\w{12}'
    __config  = []

    __description = """Share76.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = []
