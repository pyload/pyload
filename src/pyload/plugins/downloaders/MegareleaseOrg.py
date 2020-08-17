# -*- coding: utf-8 -*-

from ..base.dead_downloader import DeadDownloader


class MegareleaseOrg(DeadDownloader):
    __name__ = "MegareleaseOrg"
    __type__ = "downloader"
    __version__ = "0.07"
    __status__ = "stable"

    __pattern__ = r"https?://(?:www\.)?megarelease\.org/\w{12}"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """Megarelease.org downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("derek3x", "derek3x@vmail.me"), ("stickell", "l.stickell@yahoo.it")]
