# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class ShareFilesCo(DeadHoster):
    __name    = "ShareFilesCo"
    __type    = "hoster"
    __version = "0.02"

    __pattern = r'http://(?:www\.)?sharefiles\.co/\w{12}'

    __description = """Sharefiles.co hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("stickell", "l.stickell@yahoo.it")]
