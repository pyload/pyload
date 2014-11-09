# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class DuploadOrg(DeadHoster):
    __name__    = "DuploadOrg"
    __type__    = "hoster"
    __version__ = "0.02"

    __pattern__ = r'http://(?:www\.)?dupload\.org/\w{12}'

    __description__ = """Dupload.grg hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it")]


getInfo = create_getInfo(DuploadOrg)
