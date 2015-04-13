# -*- coding: utf-8 -*-

import re

from pyload.plugin.internal.SimpleHoster import SimpleHoster


class RgHostNet(SimpleHoster):
    __name    = "RgHostNet"
    __type    = "hoster"
    __version = "0.04"

    __pattern = r'http://(?:www\.)?rghost\.(net|ru)/[\d-]+'
    __config  = [("use_premium", "bool", "Use premium account if available", True)]

    __description = """RgHost.net hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("z00nx", "z00nx0@gmail.com")]


    INFO_PATTERN    = r'data-share42-text="(?P<N>.+?) \((?P<S>[\d.,]+) (?P<U>[\w^_]+)'
    HASHSUM_PATTERN = r'<dt>(?P<T>\w+)</dt>\s*<dd>(?P<H>\w+)'
    OFFLINE_PATTERN = r'>(File is deleted|page not found)'

    LINK_FREE_PATTERN = r'<a href="(.+?)" class="btn large'
