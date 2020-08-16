# -*- coding: utf-8 -*-

from ..downloaders.ZeveraCom import ZeveraCom


class MultihostersCom(ZeveraCom):
    __name__ = "MultihostersCom"
    __type__ = "account"
    __version__ = "0.08"
    __status__ = "testing"

    __description__ = """Multihosters.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("tjeh", "tjeh@gmx.net")]

    PLUGIN_DOMAIN = "multihosters.com"
