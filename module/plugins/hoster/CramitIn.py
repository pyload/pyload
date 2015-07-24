# -*- coding: utf-8 -*-

from module.plugins.internal.XFSHoster import XFSHoster, create_getInfo


class CramitIn(XFSHoster):
    __name__    = "CramitIn"
    __type__    = "hoster"
    __version__ = "0.08"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?cramit\.in/\w{12}'

    __description__ = """Cramit.in hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    INFO_PATTERN = r'<span class=t2>\s*(?P<N>.*?)</span>.*?<small>\s*\((?P<S>.*?)\)'

    LINK_PATTERN = r'href="(http://cramit\.in/file_download/.*?)"'


getInfo = create_getInfo(CramitIn)
