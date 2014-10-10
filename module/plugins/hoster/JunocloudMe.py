# -*- coding: utf-8 -*-

from module.plugins.internal.XFSPHoster import XFSPHoster, create_getInfo


class EasybytezCom(XFSPHoster):
    __name__ = "JunocloudMe"
    __type__ = "hoster"
    __version__ = "0.01"

    __pattern__ = r'http://(?:www\.)?easybytez\.com/\w{12}'

    __description__ = """Junoclud.me hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = ("guidobelix", "guidobelix@hotmail.it")


    HOSTER_NAME = "junocloud.me"

    FILE_INFO_PATTERN = r'<span class="name">(?P<N>.+)</span><br>\s*<span class="size">(?P<S>[^<]+)</span>'
    OFFLINE_PATTERN = r'>File not available'


getInfo = create_getInfo(JunocloudMe)
