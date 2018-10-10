# -*- coding: utf-8 -*-

from ..internal.SimpleCrypter import SimpleCrypter


class LinkSaveIn(SimpleCrypter):
    __name__ = "LinkSaveIn"
    __type__ = "crypter"
    __version__ = "2.11"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.)?linksave\.in/\w+'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("folder_per_package", "Default;Yes;No",
                   "Create folder for each package", "Default"),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """LinkSave.in decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    COOKIES = [("linksave.in", "Linksave_Language", "english")]

    OFFLINE_PATTERN = r'>(Error )?404 -'
