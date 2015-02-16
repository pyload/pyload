# -*- coding: utf-8 -*-

from pyload.plugin.account.ZeveraCom import ZeveraCom


class MultihostersCom(ZeveraCom):
    __name__    = "MultihostersCom"
    __type__    = "account"
    __version__ = "0.03"

    __description__ = """Multihosters.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("tjeh", "tjeh@gmx.net")]


    HOSTER_DOMAIN = "multihosters.com"
