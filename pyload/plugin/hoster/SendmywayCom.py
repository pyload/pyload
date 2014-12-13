# -*- coding: utf-8 -*-

from pyload.plugin.internal.XFSHoster import XFSHoster, create_getInfo


class SendmywayCom(XFSHoster):
    __name    = "SendmywayCom"
    __type    = "hoster"
    __version = "0.04"

    __pattern = r'http://(?:www\.)?sendmyway\.com/\w{12}'

    __description = """SendMyWay hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]


    HOSTER_DOMAIN = "sendmyway.com"

    NAME_PATTERN = r'<p class="file-name" ><.*?>\s*(?P<N>.+)'
    SIZE_PATTERN = r'<small>\((?P<S>\d+) bytes\)</small>'


getInfo = create_getInfo(SendmywayCom)
