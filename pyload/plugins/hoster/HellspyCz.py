# -*- coding: utf-8 -*-

from pyload.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class HellspyCz(DeadHoster):
    __name    = "HellspyCz"
    __type    = "hoster"
    __version = "0.28"

    __pattern = r'http://(?:www\.)?(?:hellspy\.(?:cz|com|sk|hu|pl)|sciagaj\.pl)(/\S+/\d+)/?.*'

    __description = """HellSpy.cz hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]


getInfo = create_getInfo(HellspyCz)
