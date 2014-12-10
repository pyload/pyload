# -*- coding: utf-8 -*-

from pyload.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class BoltsharingCom(DeadHoster):
    __name    = "BoltsharingCom"
    __type    = "hoster"
    __version = "0.02"

    __pattern = r'http://(?:www\.)?boltsharing\.com/\w{12}'

    __description = """Boltsharing.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]


getInfo = create_getInfo(BoltsharingCom)
