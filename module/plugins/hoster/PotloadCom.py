# -*- coding: utf-8 -*-
from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo


class PotloadCom(XFileSharingPro):
    __name__ = "PotloadCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:www\.)?potload\.com/\w{12}"
    __version__ = "0.01"
    __description__ = """billionuploads.com hoster plugin"""
    __author_name__ = ("stickell")
    __author_mail__ = ("l.stickell@yahoo.it")

    FILE_INFO_PATTERN = r'<h[1-6]>(?P<N>.+) \((?P<S>\d+) (?P<U>\w+)\)</h'
    HOSTER_NAME = "potload.com"


getInfo = create_getInfo(PotloadCom)
