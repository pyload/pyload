# -*- coding: utf-8 -*-
#
# Test links:
# http://hugefiles.net/prthf9ya4w6s

from module.plugins.internal.XFSPHoster import XFSPHoster, create_getInfo


class HugefilesNet(XFSPHoster):
    __name__    = "HugefilesNet"
    __type__    = "hoster"
    __version__ = "0.03"

    __pattern__ = r'http://(?:www\.)?hugefiles\.net/\w{12}'

    __description__ = """Hugefiles.net hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it")]


    HOSTER_NAME = "hugefiles.net"

    FILE_SIZE_PATTERN = r'File Size:</span>\s*<span[^>]*>(?P<S>[^<]+)</span></div>'


getInfo = create_getInfo(HugefilesNet)
