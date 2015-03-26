# -*- coding: utf-8 -*-

from pyload.plugin.account.ZeveraCom import ZeveraCom


class PutdriveCom(ZeveraCom):
    __name    = "PutdriveCom"
    __type    = "account"
    __version = "0.02"

    __description = """Putdrive.com account plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_DOMAIN = "putdrive.com"
