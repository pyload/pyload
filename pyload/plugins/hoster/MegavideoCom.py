# -*- coding: utf-8 -*-

from pyload.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class MegavideoCom(DeadHoster):
    __name    = "MegavideoCom"
    __type    = "hoster"
    __version = "0.21"

    __pattern = r'http://(?:www\.)?megavideo\.com/\?.*&?(d|v)=\w+'

    __description = """Megavideo.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("jeix", "jeix@hasnomail.de"),
                       ("mkaay", "mkaay@mkaay.de")]


getInfo = create_getInfo(MegavideoCom)
