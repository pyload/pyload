# -*- coding: utf-8 -*-

import re

from time import mktime, strptime, gmtime

from module.plugins.internal.XFSPAccount import XFSPAccount
from module.utils import parseFileSize


class RapidfileshareNet(XFSPAccount):
    __name__ = "RapidfileshareNet"
    __type__ = "account"
    __version__ = "0.01"

    __description__ = """Rapidfileshare.net account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("guidobelix", "guidobelix@hotmail.it")]


    HOSTER_URL = "http://www.rapidfileshare.net/"

