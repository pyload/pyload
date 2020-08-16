# -*- coding: utf-8 -*-

from ..base.dead_downloader import DeadDownloader


class PotloadCom(DeadDownloader):
    __name__ = "PotloadCom"
    __type__ = "downloader"
    __version__ = "0.07"
    __status__ = "stable"

    __pattern__ = r"http://(?:www\.)?potload\.com/\w{12}"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """Potload.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("stickell", "l.stickell@yahoo.it")]
