# -*- coding: utf-8 -*-

import re

from ..internal.XFSHoster import XFSHoster


class DdlTo(XFSHoster):
    __name__ = "DdlTo"
    __type__ = "hoster"
    __version__ = "0.03"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.)?ddl.to/(?P<ID>\w{12})'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool", "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Ddl.to hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    PLUGIN_DOMAIN = "ddl.to"

    URL_REPLACEMENTS = [(__pattern__ + '.*', "https://ddl.to/\g<ID>")]
    NAME_REPLACEMENTS = [(" ", ".")]

    NAME_PATTERN = r'<title>Download (?P<N>.+?)</title>'
    SIZE_PATTERN = r'<div class="name">.+?<span>(?P<S>[\d.,]+) (?P<U>[\w^_]+)</span>', re.S

    OFFLINE_PATTERN = r'<h4>File Not Found</h4>'
