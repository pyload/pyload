# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class RgHostNet(SimpleHoster):
    __name__    = "RgHostNet"
    __type__    = "hoster"
    __version__ = "0.03"

    __pattern__ = r'http://(?:www\.)?rghost\.net/\d+(?:r=\d+)?'

    __description__ = """RgHost.net hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("z00nx", "z00nx0@gmail.com")]


    INFO_PATTERN    = r'<h1>\s+(<a[^>]+>)?(?P<N>[^<]+)(</a>)?\s+<small[^>]+>\s+\((?P<S>[^)]+)\)\s+</small>\s+</h1>'
    OFFLINE_PATTERN = r'File is deleted|this page is not found'

    LINK_FREE_PATTERN = r'<a\s+href="([^"]+)"\s+class="btn\s+large\s+download"[^>]+>Download</a>'


getInfo = create_getInfo(RgHostNet)
