# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class RgHostNet(SimpleHoster):
    __name__    = "RgHostNet"
    __type__    = "hoster"
    __version__ = "0.05"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?rghost\.(net|ru)/[\d-]+'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """RgHost.net hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("z00nx", "z00nx0@gmail.com")]


    INFO_PATTERN    = r'data-share42-text="(?P<N>.+?) \((?P<S>[\d.,]+) (?P<U>[\w^_]+)'
    HASHSUM_PATTERN = r'<dt>(?P<T>\w+)</dt>\s*<dd>(?P<H>\w+)'
    OFFLINE_PATTERN = r'>(File is deleted|page not found)'

    LINK_FREE_PATTERN = r'<a href="(.+?)" class="btn large'


getInfo = create_getInfo(RgHostNet)
