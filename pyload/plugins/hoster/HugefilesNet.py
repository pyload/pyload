# -*- coding: utf-8 -*-
#
# Test links:
# http://hugefiles.net/prthf9ya4w6s

from pyload.plugins.internal.XFSHoster import XFSHoster, create_getInfo


class HugefilesNet(XFSHoster):
    __name__    = "HugefilesNet"
    __type__    = "hoster"
    __version__ = "0.04"

    __pattern__ = r'http://(?:www\.)?hugefiles\.net/\w{12}'

    __description__ = """Hugefiles.net hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it")]


    HOSTER_DOMAIN = "hugefiles.net"

    SIZE_PATTERN = r'File Size:</span>\s*<span[^>]*>(?P<S>[^<]+)</span></div>'


getInfo = create_getInfo(HugefilesNet)
