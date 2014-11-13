# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class ShareFilesCo(DeadHoster):
    __name__    = "ShareFilesCo"
    __type__    = "hoster"
    __version__ = "0.02"

    __pattern__ = r'http://(?:www\.)?sharefiles\.co/\w{12}'

    __description__ = """Sharefiles.co hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it")]


getInfo = create_getInfo(ShareFilesCo)
