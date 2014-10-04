# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class EgoFilesCom(DeadHoster):
    __name__ = "EgoFilesCom"
    __type__ = "hoster"
    __version__ = "0.16"

    __pattern__ = r'https?://(?:www\.)?egofiles\.com/\w+'

    __description__ = """Egofiles.com hoster plugin"""
    __author_name__ = "stickell"
    __author_mail__ = "l.stickell@yahoo.it"


getInfo = create_getInfo(EgoFilesCom)
