# -*- coding: utf-8 -*-

import re

from ..internal.XFSHoster import XFSHoster


class WrzucajplikiPl(XFSHoster):
    __name__ = "WrzucajplikiPl"
    __type__ = "hoster"
    __version__ = "0.03"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.)?wrzucajpliki\.pl/(?P<ID>\w{12})'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool", "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Wrzucajpliki.pl hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    NAME_PATTERN = r'name="fname" value="(?P<N>.+?)"'
    SIZE_PATTERN = r'>You have requested .+?> \((?P<S>[\d.,]+) (?P<U>[\w^_]+)\)'

    WAIT_PATTERN = r'<span class="seconds">(\d+)</span>'
    DL_LIMIT_PATTERN = r'>You have to wait (.+?) till next download<'

    OFFLINE_PATTERN = r'File Not Found|No such file with this filename'
    TEMP_OFFLINE_PATTERN = "Connection limit reached|Server error|You have reached the download limit"

    PLUGIN_DOMAIN = "wrzucajpliki.pl"