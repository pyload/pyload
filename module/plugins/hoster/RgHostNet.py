# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster


class RgHostNet(SimpleHoster):
    __name__    = "RgHostNet"
    __type__    = "hoster"
    __version__ = "0.08"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?rghost\.(net|ru)/[\d\-]+'
    __config__  = [("activated"   , "bool", "Activated"                                        , True),
                   ("use_premium" , "bool", "Use premium account if available"                 , True),
                   ("fallback"    , "bool", "Fallback to free download if premium fails"       , True),
                   ("chk_filesize", "bool", "Check file size"                                  , True),
                   ("max_wait"    , "int" , "Reconnect if waiting time is greater than minutes", 10  )]

    __description__ = """RgHost.net hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("z00nx", "z00nx0@gmail.com")]


    INFO_PATTERN    = r'data-share42-text="(?P<N>.+?) \((?P<S>[\d.,]+) (?P<U>[\w^_]+)'
    HASHSUM_PATTERN = r'<dt>(?P<H>\w+)</dt>\s*<dd>(?P<D>\w+)'
    OFFLINE_PATTERN = r'>(File is deleted|page not found)'

    LINK_FREE_PATTERN = r'<a href="(.+?)" class="btn large'
