# -*- coding: utf-8 -*-

from ..internal.DeadHoster import DeadHoster


class LetitbitNet(DeadHoster):
    __name__ = "LetitbitNet"
    __type__ = "hoster"
    __version__ = "0.39"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.)?(letitbit|shareflare)\.net/download/.+'
    __config__ = [("activated", "bool", "Activated", True)]

    __description__ = """Letitbit.net hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz"),
                   ("z00nx", "z00nx0@gmail.com")]
