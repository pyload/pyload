# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class FreevideoCz(DeadHoster):
    __name__    = "FreevideoCz"
    __type__    = "hoster"
    __version__ = "0.3"

    __pattern__ = r'http://(?:www\.)?freevideo\.cz/vase-videa/.+'

    __description__ = """Freevideo.cz hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


getInfo = create_getInfo(FreevideoCz)