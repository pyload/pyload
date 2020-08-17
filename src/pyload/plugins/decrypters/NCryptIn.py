# -*- coding: utf-8 -*-

from ..base.dead_decrypter import DeadDecrypter


class NCryptIn(DeadDecrypter):
    __name__ = "NCryptIn"
    __type__ = "decrypter"
    __version__ = "1.44"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?ncrypt\.in/(?P<TYPE>folder|link|frame)-([^/\?]+)"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """NCrypt.in decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("fragonib", "fragonib[AT]yahoo[DOT]es"),
        ("stickell", "l.stickell@yahoo.it"),
    ]
