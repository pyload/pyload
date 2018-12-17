# -*- coding: utf-8 -*-

from ..base.dead_decrypter import DeadDecrypter


class StealthTo(DeadDecrypter):
    __name__ = "StealthTo"
    __type__ = "decrypter"
    __version__ = "0.25"
    __status__ = "stable"

    __pyload_version__ = "0.5"

    __pattern__ = r"http://(?:www\.)?stealth\.to/folder/.+"
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """Stealth.to decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("spoob", "spoob@pyload.net")]
