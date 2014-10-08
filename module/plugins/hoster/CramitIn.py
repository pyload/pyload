# -*- coding: utf-8 -*-

from module.plugins.internal.XFSPHoster import XFSPHoster, create_getInfo


class CramitIn(XFSPHoster):
    __name__ = "CramitIn"
    __type__ = "hoster"
    __version__ = "0.06"

    __pattern__ = r'http://(?:www\.)?cramit\.in/\w{12}'

    __description__ = """Cramit.in hoster plugin"""
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]


    HOSTER_NAME = "cramit.in"

    FILE_INFO_PATTERN = r'<span class=t2>\s*(?P<N>.*?)</span>.*?<small>\s*\((?P<S>.*?)\)'
    LINK_PATTERN = r'href="(http://cramit.in/file_download/.*?)"'


getInfo = create_getInfo(CramitIn)
