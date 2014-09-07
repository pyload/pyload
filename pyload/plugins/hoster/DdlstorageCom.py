# -*- coding: utf-8 -*-

from pyload.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class DdlstorageCom(DeadHoster):
    __name__ = "DdlstorageCom"
    __type__ = "hoster"
    __version__ = "1.02"

    __pattern__ = r'https?://(?:www\.)?ddlstorage\.com/\w+'

    __description__ = """DDLStorage.com hoster plugin"""
    __author_name__ = ("zoidberg", "stickell")
    __author_mail__ = ("zoidberg@mujmail.cz", "l.stickell@yahoo.it")


getInfo = create_getInfo(DdlstorageCom)
