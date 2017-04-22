# -*- coding: utf-8 -*-

from ..internal.DeadHoster import DeadHoster


class HotfileCom(DeadHoster):
    __name__ = "HotfileCom"
    __type__ = "hoster"
    __version__ = "0.42"
    __status__ = "stable"

    __pattern__ = r'https?://(?:www\.)?hotfile\.com/dl/\d+/\w+'
    __config__ = []  # @TODO: Remove in 0.4.10

    __description__ = """Hotfile.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("sitacuisses", "sitacuisses@yhoo.de"),
                   ("spoob", "spoob@pyload.org"),
                   ("mkaay", "mkaay@mkaay.de"),
                   ("JoKoT3", "jokot3@gmail.com")]
