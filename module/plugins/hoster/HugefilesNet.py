# -*- coding: utf-8 -*-
#
# Test links:
# http://hugefiles.net/prthf9ya4w6s

from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo


class HugefilesNet(XFileSharingPro):
    __name__ = "HugefilesNet"
    __type__ = "hoster"
    __version__ = "0.01"

    __pattern__ = r'http://(?:www\.)?hugefiles\.net/\w{12}'

    __description__ = """Hugefiles.net hoster plugin"""
    __author_name__ = "stickell"
    __author_mail__ = "l.stickell@yahoo.it"

    HOSTER_NAME = "hugefiles.net"

    FILE_SIZE_PATTERN = r'File Size:</span>\s*<span[^>]*>(?P<S>[^<]+)</span></div>'


getInfo = create_getInfo(HugefilesNet)
