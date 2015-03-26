# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class BoltsharingCom(DeadHoster):
    __name    = "BoltsharingCom"
    __type    = "hoster"
    __version = "0.02"

    __pattern = r'http://(?:www\.)?boltsharing\.com/\w{12}'
    __config  = []

    __description = """Boltsharing.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]
