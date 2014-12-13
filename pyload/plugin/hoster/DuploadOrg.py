# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster, create_getInfo


class DuploadOrg(DeadHoster):
    __name    = "DuploadOrg"
    __type    = "hoster"
    __version = "0.02"

    __pattern = r'http://(?:www\.)?dupload\.org/\w{12}'

    __description = """Dupload.grg hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("stickell", "l.stickell@yahoo.it")]


getInfo = create_getInfo(DuploadOrg)
