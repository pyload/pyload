# -*- coding: utf-8 -*-

from module.plugins.accounts.ZeveraCom import ZeveraCom


class MultihostersCom(ZeveraCom):
    __name__    = "MultihostersCom"
    __type__    = "account"
    __version__ = "0.07"
    __status__  = "testing"

    __description__ = """Multihosters.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("tjeh", "tjeh@gmx.net")]


    PLUGIN_DOMAIN = "multihosters.com"
