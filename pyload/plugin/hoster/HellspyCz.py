# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class HellspyCz(DeadHoster):
    __name    = "HellspyCz"
    __type    = "hoster"
    __version = "0.28"

    __pattern = r'http://(?:www\.)?(?:hellspy\.(?:cz|com|sk|hu|pl)|sciagaj\.pl)(/\S+/\d+)'
    __config  = []

    __description = """HellSpy.cz hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]
