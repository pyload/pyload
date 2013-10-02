# -*- coding: utf-8 -*-
from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo


class Share76Com(XFileSharingPro):
    __name__ = "Share76Com"
    __type__ = "hoster"
    __pattern__ = r"http://(?:\w*\.)*?share76.com/\w{12}"
    __version__ = "0.04"
    __description__ = """share76.com hoster plugin"""
    __author_name__ = ("me")

    FILE_INFO_PATTERN = r'<h2>\s*File:\s*<font[^>]*>(?P<N>[^>]+)</font>\s*\[<font[^>]*>(?P<S>[0-9.]+) (?P<U>[kKMG])i?B</font>\]</h2>'
    HOSTER_NAME = "share76.com"


getInfo = create_getInfo(Share76Com)
