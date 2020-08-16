# -*- coding: utf-8 -*-

from ..base.simple_decrypter import SimpleDecrypter


class FilestubeCom(SimpleDecrypter):
    __name__ = "FilestubeCom"
    __type__ = "decrypter"
    __version__ = "0.11"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?filestube\.(?:com|to)/\w+"
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

    __description__ = """Filestube.com decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("stickell", "l.stickell@yahoo.it")]

    LINK_PATTERN = (
        r"<a class=\"file-link-main(?: noref)?\" [^>]* href=\"(http://[^\"]+)"
    )
    NAME_PATTERN = r"<h1\s*> (?P<N>.+?)  download\s*</h1>"
