# -*- coding: utf-8 -*-

import re

from pyload.plugin.internal.XFSHoster import XFSHoster, create_getInfo


class HugefilesNet(XFSHoster):
    __name    = "HugefilesNet"
    __type    = "hoster"
    __version = "0.05"

    __pattern = r'http://(?:www\.)?hugefiles\.net/\w{12}'

    __description = """Hugefiles.net hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("stickell", "l.stickell@yahoo.it")]


    HOSTER_DOMAIN = "hugefiles.net"

    SIZE_PATTERN = r'File Size:</span>\s*<span[^>]*>(?P<S>[^<]+)</span></div>'

    FORM_INPUTS_MAP = {'ctype': re.compile(r'\d+')}


getInfo = create_getInfo(HugefilesNet)
