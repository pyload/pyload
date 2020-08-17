# -*- coding: utf-8 -*-

from .ZeveraCom import ZeveraCom


class PutdriveCom(ZeveraCom):
    __name__ = "PutdriveCom"
    __type__ = "downloader"
    __version__ = "0.07"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)putdrive\.com/(getFiles\.ashx|Members/download\.ashx)\?.*ourl=.+"
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """Multihosters.com multi-downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]
