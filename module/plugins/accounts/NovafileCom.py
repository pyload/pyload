# -*- coding: utf-8 -*-

from module.plugins.internal.XFSPAccount import XFSPAccount


class NovafileCom(XFSPAccount):
    __name__ = "NovafileCom"
    __type__ = "account"
    __version__ = "0.01"

    __description__ = """Novafile.com account plugin"""
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_URL = "http://www.novafile.com/"
