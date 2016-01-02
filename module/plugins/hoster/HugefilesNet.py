# -*- coding: utf-8 -*-

import re

from module.plugins.internal.XFSHoster import XFSHoster


class HugefilesNet(XFSHoster):
    __name__    = "HugefilesNet"
    __type__    = "hoster"
    __version__ = "0.10"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?hugefiles\.net/\w{12}'
    __config__  = [("activated"   , "bool", "Activated"                                        , True),
                   ("use_premium" , "bool", "Use premium account if available"                 , True),
                   ("fallback"    , "bool", "Fallback to free download if premium fails"       , True),
                   ("chk_filesize", "bool", "Check file size"                                  , True),
                   ("max_wait"    , "int" , "Reconnect if waiting time is greater than minutes", 10  )]

    __description__ = """Hugefiles.net hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it")]


    PLUGIN_DOMAIN = "hugefiles.net"

    SIZE_PATTERN = r'File Size:</span>\s*<span.*?>(?P<S>.+?)</span></div>'

    FORM_INPUTS_MAP = {'ctype': re.compile(r'\d+')}
