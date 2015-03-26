# -*- coding: utf-8 -*-

from pyload.plugin.internal.XFSHoster import XFSHoster


class CramitIn(XFSHoster):
    __name    = "CramitIn"
    __type    = "hoster"
    __version = "0.07"

    __pattern = r'http://(?:www\.)?cramit\.in/\w{12}'

    __description = """Cramit.in hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]


    INFO_PATTERN = r'<span class=t2>\s*(?P<N>.*?)</span>.*?<small>\s*\((?P<S>.*?)\)'

    LINK_PATTERN = r'href="(http://cramit\.in/file_download/.*?)"'
