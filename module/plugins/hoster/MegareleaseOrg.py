# -*- coding: utf-8 -*-
from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo

class MegareleaseOrg(XFileSharingPro):
    __name__ = "MegareleaseOrg"
    __type__ = "hoster"
    __pattern__ = r"http://(?:\w*\.)*?megarelease.org/\w{12}"
    __version__ = "0.01"
    __description__ = """Megarelease.Org hoster plugin"""
    __author_name__ = ("derek3x")
    __author_mail__ = ("derek3x@vmail.me")

    FILE_NAME_PATTERN = r'<font color="red">http://.*?/.*?/(?P<N>.*?)</font>'
    FILE_SIZE_PATTERN = r'</font> \((?P<S>.*?)\)</font>'
    HOSTER_NAME = "megarelease.org"

getInfo = create_getInfo(MegareleaseOrg)
