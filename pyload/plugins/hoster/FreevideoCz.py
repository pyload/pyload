# -*- coding: utf-8 -*-

from pyload.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class FreevideoCz(DeadHoster):
    __name__ = "FreevideoCz"
    __type__ = "hoster"
    __version__ = "0.3"

    __pattern__ = r'http://(?:www\.)?freevideo\.cz/vase-videa/.+'

    __description__ = """Freevideo.cz hoster plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"


getInfo = create_getInfo(FreevideoCz)