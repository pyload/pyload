# -*- coding: utf-8 -*-

import re

from module.plugins.internal.XFSHoster import XFSHoster, create_getInfo


class HugefilesNet(XFSHoster):
    __name__    = "HugefilesNet"
    __type__    = "hoster"
    __version__ = "0.06"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?hugefiles\.net/\w{12}'

    __description__ = """Hugefiles.net hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it")]


    SIZE_PATTERN = r'File Size:</span>\s*<span.*?>(?P<S>[^<]+)</span></div>'

    FORM_INPUTS_MAP = {'ctype': re.compile(r'\d+')}


getInfo = create_getInfo(HugefilesNet)
