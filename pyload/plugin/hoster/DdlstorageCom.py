# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class DdlstorageCom(DeadHoster):
    __name    = "DdlstorageCom"
    __type    = "hoster"
    __version = "1.02"

    __pattern = r'https?://(?:www\.)?ddlstorage\.com/\w+'

    __description = """DDLStorage.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("stickell", "l.stickell@yahoo.it")]
