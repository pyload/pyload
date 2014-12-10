# -*- coding: utf-8 -*-

from pyload.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class TurbouploadCom(DeadHoster):
    __name    = "TurbouploadCom"
    __type    = "hoster"
    __version = "0.03"

    __pattern = r'http://(?:www\.)?turboupload\.com/(\w+).*'

    __description = """Turboupload.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]


getInfo = create_getInfo(TurbouploadCom)
