# -*- coding: utf-8 -*-

from pyload.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class SpeedLoadOrg(DeadHoster):
    __name__ = "SpeedLoadOrg"
    __type__ = "hoster"
    __version__ = "1.02"

    __pattern__ = r'http://(?:www\.)?speedload\.org/(?P<ID>\w+)'

    __description__ = """Speedload.org hoster plugin"""
    __author_name__ = "stickell"
    __author_mail__ = "l.stickell@yahoo.it"


getInfo = create_getInfo(SpeedLoadOrg)
