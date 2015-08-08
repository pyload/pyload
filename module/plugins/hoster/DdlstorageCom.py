# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class DdlstorageCom(DeadHoster):
    __name__    = "DdlstorageCom"
    __type__    = "hoster"
    __version__ = "1.03"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?ddlstorage\.com/\w+'
    __config__  = []  #@TODO: Remove in 0.4.10

    __description__ = """DDLStorage.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("stickell", "l.stickell@yahoo.it")]


getInfo = create_getInfo(DdlstorageCom)
