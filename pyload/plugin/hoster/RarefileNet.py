# -*- coding: utf-8 -*-

import re

from pyload.plugin.internal.XFSHoster import XFSHoster, create_getInfo


class RarefileNet(XFSHoster):
    __name    = "RarefileNet"
    __type    = "hoster"
    __version = "0.08"

    __pattern = r'http://(?:www\.)?rarefile\.net/\w{12}'

    __description = """Rarefile.net hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]


    HOSTER_DOMAIN = "rarefile.net"

    NAME_PATTERN = r'<font color="red">(?P<N>.+?)<'
    SIZE_PATTERN = r'>Size : (?P<S>[\d.,]+) (?P<U>[\w^_]+)'

    LINK_PATTERN = r'<a href="(?P<link>[^"]+)">(?P=link)</a>'


getInfo = create_getInfo(RarefileNet)
