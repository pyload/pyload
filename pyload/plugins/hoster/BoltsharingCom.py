# -*- coding: utf-8 -*-

from pyload.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class BoltsharingCom(DeadHoster):
    __name__ = "BoltsharingCom"
    __type__ = "hoster"
    __version__ = "0.02"

    __pattern__ = r'http://(?:www\.)?boltsharing.com/\w{12}'

    __description__ = """Boltsharing.com hoster plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"


getInfo = create_getInfo(BoltsharingCom)
