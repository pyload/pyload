# -*- coding: utf-8 -*-

import re

from pyload.plugin.internal.SimpleHoster import SimpleHoster, create_getInfo


class RgHostNet(SimpleHoster):
    __name    = "RgHostNet"
    __type    = "hoster"
    __version = "0.03"

    __pattern = r'http://(?:www\.)?rghost\.net/\d+(?:r=\d+)?'

    __description = """RgHost.net hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("z00nx", "z00nx0@gmail.com")]


    INFO_PATTERN    = r'<h1>\s+(<a[^>]+>)?(?P<N>[^<]+)(</a>)?\s+<small[^>]+>\s+\((?P<S>[^)]+)\)\s+</small>\s+</h1>'
    OFFLINE_PATTERN = r'File is deleted|this page is not found'

    LINK_FREE_PATTERN = r'<a\s+href="([^"]+)"\s+class="btn\s+large\s+download"[^>]+>Download</a>'


getInfo = create_getInfo(RgHostNet)
