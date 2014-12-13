# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster, create_getInfo


class PotloadCom(DeadHoster):
    __name    = "PotloadCom"
    __type    = "hoster"
    __version = "0.02"

    __pattern = r'http://(?:www\.)?potload\.com/\w{12}'

    __description = """Potload.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("stickell", "l.stickell@yahoo.it")]


getInfo = create_getInfo(PotloadCom)
