# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class ShareFilesCo(DeadHoster):
    __name__ = "ShareFilesCo"
    __type__ = "hoster"
    __version__ = "0.02"

    __pattern__ = r'http://(?:www\.)?sharefiles\.co/\w{12}'

    __description__ = """Sharefiles.co hoster plugin"""
    __author_name__ = "stickell"
    __author_mail__ = "l.stickell@yahoo.it"


getInfo = create_getInfo(ShareFilesCo)
