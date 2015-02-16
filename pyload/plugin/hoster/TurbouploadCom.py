# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class TurbouploadCom(DeadHoster):
    __name    = "TurbouploadCom"
    __type    = "hoster"
    __version = "0.03"

    __pattern = r'http://(?:www\.)?turboupload\.com/(\w+)'

    __description = """Turboupload.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]
