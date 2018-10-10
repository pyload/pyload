# -*- coding: utf-8 -*-

from ..internal.SimpleCrypter import SimpleCrypter


class NosvideoCom(SimpleCrypter):
    __name__ = "NosvideoCom"
    __type__ = "crypter"
    __version__ = "0.08"
    __status__ = "testing"

    __pattern__ = r'http://(?:www\.)?nosvideo\.com/\?v=\w+'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("folder_per_package", "Default;Yes;No",
                   "Create folder for each package", "Default"),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Nosvideo.com decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("igel", "igelkun@myopera.com")]

    LINK_PATTERN = r'href="(http://(?:w{3}\.)?nosupload\.com/\?d=\w+)"'
    NAME_PATTERN = r'<[tT]itle>Watch (?P<N>.+?)<'
