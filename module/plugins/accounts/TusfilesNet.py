# -*- coding: utf-8 -*-

import re

from time import mktime, strptime, gmtime

from module.plugins.internal.XFSAccount import XFSAccount


class TusfilesNet(XFSAccount):
    __name__    = "TusfilesNet"
    __type__    = "account"
    __version__ = "0.06"

    __description__ = """ Tusfile.net account plugin """
    __license__     = "GPLv3"
    __authors__     = [("guidobelix", "guidobelix@hotmail.it")]


    HOSTER_DOMAIN = "tusfiles.net"

    VALID_UNTIL_PATTERN = r'<span class="label label-default">([^<]+)</span>'
    TRAFFIC_LEFT_PATTERN = r'<td><img src="//www\.tusfiles\.net/i/icon/meter\.png" alt=""/></td>\n<td>&nbsp;(?P<S>[\d.,]+)'
