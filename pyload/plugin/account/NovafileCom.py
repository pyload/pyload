# -*- coding: utf-8 -*-

from pyload.plugin.internal.XFSAccount import XFSAccount


class NovafileCom(XFSAccount):
    __name    = "NovafileCom"
    __type    = "account"
    __version = "0.02"

    __description = """Novafile.com account plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_DOMAIN = "novafile.com"
