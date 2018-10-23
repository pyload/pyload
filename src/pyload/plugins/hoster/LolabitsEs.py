# -*- coding: utf-8 -*

from ..internal.deadhoster import DeadHoster


class LolabitsEs(DeadHoster):
    __name__ = "LolabitsEs"
    __type__ = "hoster"
    __version__ = "0.08"
    __status__ = "stable"

    __pyload_version__ = "0.5"

    __pattern__ = r"https?://(?:www\.)?lolabits\.es/.+"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """Lolabits.es hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zapp-brannigan", "fuerst.reinje@web.de")]
