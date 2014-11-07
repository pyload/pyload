# -*- coding: utf-8 -*-

from module.plugins.internal.XFSHoster import XFSHoster, create_getInfo


class SendmywayCom(XFSHoster):
    __name__    = "SendmywayCom"
    __type__    = "hoster"
    __version__ = "0.04"

    __pattern__ = r'http://(?:www\.)?sendmyway\.com/\w{12}'

    __description__ = """SendMyWay hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    HOSTER_DOMAIN = "sendmyway.com"

    NAME_PATTERN = r'<p class="file-name" ><.*?>\s*(?P<N>.+)'
    SIZE_PATTERN = r'<small>\((?P<S>\d+) bytes\)</small>'


getInfo = create_getInfo(SendmywayCom)
