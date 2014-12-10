# -*- coding: utf-8 -*-

from pyload.plugins.internal.XFSHoster import XFSHoster, create_getInfo


class CramitIn(XFSHoster):
    __name    = "CramitIn"
    __type    = "hoster"
    __version = "0.07"

    __pattern = r'http://(?:www\.)?cramit\.in/\w{12}'

    __description = """Cramit.in hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]


    HOSTER_DOMAIN = "cramit.in"

    INFO_PATTERN = r'<span class=t2>\s*(?P<N>.*?)</span>.*?<small>\s*\((?P<S>.*?)\)'
    LINK_PATTERN = r'href="(http://cramit\.in/file_download/.*?)"'


getInfo = create_getInfo(CramitIn)
