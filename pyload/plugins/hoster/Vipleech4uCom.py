# -*- coding: utf-8 -*-

from pyload.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class Vipleech4uCom(DeadHoster):
    __name    = "Vipleech4uCom"
    __type    = "hoster"
    __version = "0.20"

    __pattern = r'http://(?:www\.)?vipleech4u\.com/manager\.php'

    __description = """Vipleech4u.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("Kagenoshin", "kagenoshin@gmx.ch")]


getInfo = create_getInfo(Vipleech4uCom)
