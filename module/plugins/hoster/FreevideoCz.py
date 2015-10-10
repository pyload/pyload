# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class FreevideoCz(DeadHoster):
    __name__    = "FreevideoCz"
    __type__    = "hoster"
    __version__ = "0.31"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?freevideo\.cz/vase-videa/.+'
    __config__  = []  #@TODO: Remove in 0.4.10

    __description__ = """Freevideo.cz hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


getInfo = create_getInfo(FreevideoCz)