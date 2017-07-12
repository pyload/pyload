# -*- coding: utf-8 -*-

from ..internal.SimpleCrypter import SimpleCrypter


class FshareVnFolder(SimpleCrypter):
    __name__ = "FshareVnFolder"
    __type__ = "crypter"
    __version__ = "0.08"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.)?fshare\.vn/folder/.+'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("folder_per_package", "Default;Yes;No", "Create folder for each package", "Default"),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Fshare.vn folder decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz"),
                   ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    OFFLINE_PATTERN = r'404</title>'
    LINK_PATTERN = r'<a class="filename" .+? href="(.+?)"'

    URL_REPLACEMENTS = [("http://", "https://")]
