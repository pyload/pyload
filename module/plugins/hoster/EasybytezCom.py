# -*- coding: utf-8 -*-

from module.plugins.internal.XFSPHoster import XFSPHoster, create_getInfo


class EasybytezCom(XFSPHoster):
    __name__ = "EasybytezCom"
    __type__ = "hoster"
    __version__ = "0.21"

    __pattern__ = r'http://(?:www\.)?easybytez\.com/\w{12}'

    __description__ = """Easybytez.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz"),
                   ("stickell", "l.stickell@yahoo.it")]


    HOSTER_NAME = "easybytez.com"

    FILE_INFO_PATTERN = r'<span class="name">(?P<N>.+)</span><br>\s*<span class="size">(?P<S>[^<]+)</span>'
    OFFLINE_PATTERN = r'>File not available'

    LINK_PATTERN = r'(http://(\w+\.(easybytez|easyload|ezbytez|zingload)\.(com|to)|\d+\.\d+\.\d+\.\d+)/files/\d+/\w+/.+?)["\'<]'


getInfo = create_getInfo(EasybytezCom)
