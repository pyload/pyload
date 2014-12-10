# -*- coding: utf-8 -*-

import re

from time import mktime, strptime, gmtime

from pyload.plugins.internal.XFSAccount import XFSAccount


class TusfilesNet(XFSAccount):
    __name    = "TusfilesNet"
    __type    = "account"
    __version = "0.06"

    __description = """Tusfile.net account plugin"""
    __license     = "GPLv3"
    __authors     = [("guidobelix", "guidobelix@hotmail.it")]


    HOSTER_DOMAIN = "tusfiles.net"

    VALID_UNTIL_PATTERN = r'<span class="label label-default">([^<]+)</span>'
    TRAFFIC_LEFT_PATTERN = r'<td><img src="//www\.tusfiles\.net/i/icon/meter\.png" alt=""/></td>\n<td>&nbsp;(?P<S>[\d.,]+)'
