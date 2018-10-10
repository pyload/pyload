# -*- coding: utf-8 -*-

from ..internal.DeadHoster import DeadHoster


class FiredriveCom(DeadHoster):
    __name__ = "FiredriveCom"
    __type__ = "hoster"
    __version__ = "0.11"
    __status__ = "stable"

    __pattern__ = r'https?://(?:www\.)?(firedrive|putlocker)\.com/(mobile/)?(file|embed)/(?P<ID>\w+)'
    __config__ = []  # @TODO: Remove in 0.4.10

    __description__ = """Firedrive.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]
