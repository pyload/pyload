# -*- coding: utf-8 -*-
from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo


class UptoboxCom(XFileSharingPro):
    __name__ = "UptoboxCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:\w*\.)*?uptobox.com/\w{12}"
    __version__ = "0.07"
    __description__ = """Uptobox.com hoster plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"

    FILE_INFO_PATTERN = r'<div class="para_title">(?P<N>.+) \((?P<S>[^)]+)\)</div>'
    FILE_OFFLINE_PATTERN = r'<center>File Not Found</center>'
    HOSTER_NAME = "uptobox.com"


getInfo = create_getInfo(UptoboxCom)
