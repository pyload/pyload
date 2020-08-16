# -*- coding: utf-8 -*-

from ..base.dead_downloader import DeadDownloader


class FileshareInUa(DeadDownloader):
    __name__ = "FileshareInUa"
    __type__ = "downloader"
    __version__ = "0.07"
    __status__ = "stable"

    __pattern__ = r"https?://(?:www\.)?fileshare\.in\.ua/\w{7}"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """Fileshare.in.ua downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("fwannmacher", "felipe@warhammerproject.com")]
