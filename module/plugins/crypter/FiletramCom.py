# -*- coding: utf-8 -*-

from ..internal.SimpleCrypter import SimpleCrypter


class FiletramCom(SimpleCrypter):
    __name__ = "FiletramCom"
    __type__ = "crypter"
    __version__ = "0.08"
    __status__ = "testing"

    __pattern__ = r'http://(?:www\.)?filetram\.com/[^/]+/.+'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("folder_per_package", "Default;Yes;No",
                   "Create folder for each package", "Default"),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Filetram.com decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("igel", "igelkun@myopera.com"),
                   ("stickell", "l.stickell@yahoo.it")]

    LINK_PATTERN = r'\s+(http://.+)'
    NAME_PATTERN = r'<title>(?P<N>.+?) - Free Download'
