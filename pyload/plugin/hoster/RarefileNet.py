# -*- coding: utf-8 -*-

import re

from pyload.plugin.internal.XFSHoster import XFSHoster


class RarefileNet(XFSHoster):
    __name    = "RarefileNet"
    __type    = "hoster"
    __version = "0.09"

    __pattern = r'http://(?:www\.)?rarefile\.net/\w{12}'

    __description = """Rarefile.net hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]


    LINK_PATTERN = r'<a href="(.+?)">\1</a>'
