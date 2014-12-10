# -*- coding: utf-8 -*-

from pyload.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class Share76Com(DeadHoster):
    __name    = "Share76Com"
    __type    = "hoster"
    __version = "0.04"

    __pattern = r'http://(?:www\.)?share76\.com/\w{12}'

    __description = """Share76.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = []


getInfo = create_getInfo(Share76Com)
