# -*- coding: utf-8 -*-

from ..base.simple_decrypter import SimpleDecrypter


class FilecloudIoFolder(SimpleDecrypter):
    __name__ = "FilecloudIoFolder"
    __type__ = "decrypter"
    __version__ = "0.09"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?(filecloud\.io|ifile\.it)/_\w+"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        (
            "folder_per_package",
            "Default;Yes;No",
            "Create folder for each package",
            "Default",
        ),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Filecloud.io folder decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    LINK_PATTERN = r'href="(http://filecloud\.io/\w+)" title'
    NAME_PATTERN = r">(?P<N>.+?) - filecloud\.io<"
