# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class Vipleech4UCom(DeadHoster):
    __name    = "Vipleech4UCom"
    __type    = "hoster"
    __version = "0.20"

    __pattern = r'http://(?:www\.)?vipleech4u\.com/manager\.php'
    __config  = []

    __description = """Vipleech4u.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("Kagenoshin", "kagenoshin@gmx.ch")]
