# -*- coding: utf-8 -*-

from module.plugins.internal.XFSHoster import XFSHoster, create_getInfo


class EasybytezCom(XFSHoster):
    __name__    = "EasybytezCom"
    __type__    = "hoster"
    __version__ = "0.24"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?easybytez\.com/\w{12}'

    __description__ = """Easybytez.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("stickell", "l.stickell@yahoo.it")]


    OFFLINE_PATTERN = r'>File not available'

    LINK_PATTERN = r'(http://(\w+\.(easybytez|easyload|ezbytez|zingload)\.(com|to)|\d+\.\d+\.\d+\.\d+)/files/\d+/\w+/.+?)["\'<]'


getInfo = create_getInfo(EasybytezCom)
