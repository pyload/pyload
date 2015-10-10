# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class TurbouploadCom(DeadHoster):
    __name__    = "TurbouploadCom"
    __type__    = "hoster"
    __version__ = "0.04"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?turboupload\.com/(\w+)'
    __config__  = []  #@TODO: Remove in 0.4.10

    __description__ = """Turboupload.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


getInfo = create_getInfo(TurbouploadCom)
