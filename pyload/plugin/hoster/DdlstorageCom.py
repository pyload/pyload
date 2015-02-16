# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class DdlstorageCom(DeadHoster):
    __name__    = "DdlstorageCom"
    __type__    = "hoster"
    __version__ = "1.02"

    __pattern__ = r'https?://(?:www\.)?ddlstorage\.com/\w+'

    __description__ = """DDLStorage.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("stickell", "l.stickell@yahoo.it")]
