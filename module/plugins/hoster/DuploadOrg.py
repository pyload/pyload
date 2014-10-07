# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class DuploadOrg(DeadHoster):
    __name__ = "DuploadOrg"
    __type__ = "hoster"
    __version__ = "0.02"

    __pattern__ = r'http://(?:www\.)?dupload\.org/\w{12}'

    __description__ = """Dupload.grg hoster plugin"""
    __author_name__ = "stickell"
    __author_mail__ = "l.stickell@yahoo.it"


getInfo = create_getInfo(DuploadOrg)
