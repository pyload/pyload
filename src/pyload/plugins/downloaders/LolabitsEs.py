# -*- coding: utf-8 -*

from ..base.dead_downloader import DeadDownloader


class LolabitsEs(DeadDownloader):
    __name__ = "LolabitsEs"
    __type__ = "downloader"
    __version__ = "0.08"
    __status__ = "stable"

    __pattern__ = r"https?://(?:www\.)?lolabits\.es/.+"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """Lolabits.es downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zapp-brannigan", "fuerst.reinje@web.de")]
