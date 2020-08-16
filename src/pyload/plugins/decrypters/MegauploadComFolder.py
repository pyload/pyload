# -*- coding: utf-8 -*-

from ..base.dead_decrypter import DeadDecrypter


class MegauploadComFolder(DeadDecrypter):
    __name__ = "MegauploadComFolder"
    __type__ = "decrypter"
    __version__ = "0.08"
    __status__ = "stable"

    __pattern__ = (
        r"http://(?:www\.)?megaupload\.com/(\?f|xml/folderfiles\.php\?.*&?folderid)=\w+"
    )
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """Megaupload.com folder decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]
