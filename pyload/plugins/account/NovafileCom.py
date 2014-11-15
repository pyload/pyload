# -*- coding: utf-8 -*-

from pyload.plugins.internal.XFSAccount import XFSAccount


class NovafileCom(XFSAccount):
    __name__    = "NovafileCom"
    __type__    = "account"
    __version__ = "0.02"

    __description__ = """Novafile.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_DOMAIN = "novafile.com"
