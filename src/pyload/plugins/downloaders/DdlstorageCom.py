# -*- coding: utf-8 -*-

from ..base.dead_downloader import DeadDownloader


class DdlstorageCom(DeadDownloader):
    __name__ = "DdlstorageCom"
    __type__ = "downloader"
    __version__ = "1.07"
    __status__ = "stable"

    __pattern__ = r"https?://(?:www\.)?ddlstorage\.com/\w+"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """DDLStorage.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("zoidberg", "zoidberg@mujmail.cz"),
        ("stickell", "l.stickell@yahoo.it"),
    ]
