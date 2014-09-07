# -*- coding: utf-8 -*-

from pyload.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo


class MegareleaseOrg(XFileSharingPro):
    __name__ = "MegareleaseOrg"
    __type__ = "hoster"
    __version__ = "0.01"

    __pattern__ = r'https?://(?:www\.)?megarelease.org/\w{12}'

    __description__ = """Megarelease.org hoster plugin"""
    __author_name__ = ("derek3x", "stickell")
    __author_mail__ = ("derek3x@vmail.me", "l.stickell@yahoo.it")

    HOSTER_NAME = "megarelease.org"

    FILE_INFO_PATTERN = r'<font color="red">%s/(?P<N>.+)</font> \((?P<S>[^)]+)\)</font>' % __pattern__


getInfo = create_getInfo(MegareleaseOrg)
