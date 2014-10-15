# -*- coding: utf-8 -*-

import re

from time import mktime, strptime, gmtime

from module.plugins.internal.XFSPAccount import XFSPAccount
from module.utils import parseFileSize


class TusfilesNet(XFSPAccount):
    __name__ = "TusfilesNet"
    __type__ = "account"
    __version__ = "0.03"

    __description__ = """ Tusfile.net account plugin """
    __license__ = "GPLv3"
    __authors__ = [("guidobelix", "guidobelix@hotmail.it")]


    HOSTER_URL = "http://www.tusfiles.net/"

    VALID_UNTIL_PATTERN = r'<span class="label label-default">([^<]+)</span>'
    TRAFFIC_LEFT_PATTERN = r'<td><img src="//www\.tusfiles\.net/i/icon/meter\.png" alt=""/></td>\n<td>&nbsp;(?P<S>[^<]+)</td>'
