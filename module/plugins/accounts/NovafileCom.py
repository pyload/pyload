# -*- coding: utf-8 -*-

from module.plugins.internal.XFSAccount import XFSAccount


class NovafileCom(XFSAccount):
    __name__    = "NovafileCom"
    __type__    = "account"
    __version__ = "0.03"
    __status__  = "testing"

    __description__ = """Novafile.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_DOMAIN = "novafile.com"
