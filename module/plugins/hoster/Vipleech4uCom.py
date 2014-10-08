# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class Vipleech4uCom(DeadHoster):
    __name__ = "Vipleech4uCom"
    __type__ = "hoster"
    __version__ = "0.2"

    __pattern__ = r'http://(?:www\.)?vipleech4u\.com/manager\.php'

    __description__ = """Vipleech4u.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Kagenoshin", "kagenoshin@gmx.ch")]


getInfo = create_getInfo(Vipleech4uCom)
