# -*- coding: utf-8 -*-

from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo


class DdlstorageCom(XFileSharingPro):
    __name__ = "DdlstorageCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:\w*\.)*?ddlstorage.com/\w{12}"
    __version__ = "0.07"
    __description__ = """DDLStorage.com hoster plugin"""
    __author_name__ = ("zoidberg", "stickell")
    __author_mail__ = ("zoidberg@mujmail.cz", "l.stickell@yahoo.it")

    FILE_INFO_PATTERN = r'<p class="sub_title"[^>]*>(?P<N>.+) \((?P<S>[^)]+)\)</p>'
    HOSTER_NAME = "ddlstorage.com"


getInfo = create_getInfo(DdlstorageCom)