# -*- coding: utf-8 -*-

from module.plugins.internal.XFSPHoster import XFSPHoster, create_getInfo


class SendmywayCom(XFSPHoster):
    __name__ = "SendmywayCom"
    __type__ = "hoster"
    __version__ = "0.03"

    __pattern__ = r'http://(?:www\.)?sendmyway\.com/\w{12}'

    __description__ = """SendMyWay hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]


    HOSTER_NAME = "sendmyway.com"

    FILE_NAME_PATTERN = r'<p class="file-name" ><.*?>\s*(?P<N>.+)'
    FILE_SIZE_PATTERN = r'<small>\((?P<S>\d+) bytes\)</small>'


getInfo = create_getInfo(SendmywayCom)
