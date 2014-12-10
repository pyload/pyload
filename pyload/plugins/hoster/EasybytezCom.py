# -*- coding: utf-8 -*-

from pyload.plugins.internal.XFSHoster import XFSHoster, create_getInfo


class EasybytezCom(XFSHoster):
    __name    = "EasybytezCom"
    __type    = "hoster"
    __version = "0.23"

    __pattern = r'http://(?:www\.)?easybytez\.com/\w{12}'

    __description = """Easybytez.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("stickell", "l.stickell@yahoo.it")]


    HOSTER_DOMAIN = "easybytez.com"

    OFFLINE_PATTERN = r'>File not available'

    LINK_PATTERN = r'(http://(\w+\.(easybytez|easyload|ezbytez|zingload)\.(com|to)|\d+\.\d+\.\d+\.\d+)/files/\d+/\w+/.+?)["\'<]'


getInfo = create_getInfo(EasybytezCom)
