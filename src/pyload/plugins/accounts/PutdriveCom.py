# -*- coding: utf-8 -*-

from ..downloaders.ZeveraCom import ZeveraCom


class PutdriveCom(ZeveraCom):
    __name__ = "PutdriveCom"
    __type__ = "account"
    __version__ = "0.07"
    __status__ = "testing"

    __description__ = """Putdrive.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    PLUGIN_DOMAIN = "putdrive.com"
