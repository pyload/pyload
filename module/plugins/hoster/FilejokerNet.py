# -*- coding: utf-8 -*-

import re

from module.plugins.internal.XFSHoster import XFSHoster


class FilejokerNet(XFSHoster):
    __name__    = "FilejokerNet"
    __type__    = "hoster"
    __version__ = "0.02"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?filejoker\.net/\w{12}'
    __config__  = [("activated"   , "bool", "Activated"                                        , True),
                   ("use_premium" , "bool", "Use premium account if available"                 , True),
                   ("fallback"    , "bool", "Fallback to free download if premium fails"       , True),
                   ("chk_filesize", "bool", "Check file size"                                  , True),
                   ("max_wait"    , "int" , "Reconnect if waiting time is greater than minutes", 10  )]

    __description__ = """Filejoker.net hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]


    PLUGIN_DOMAIN   = "filejoker.net"

    WAIT_PATTERN      = r'Please [Ww]ait (?:<span id="count" class="alert-success">)?([\w ]+?)(?:</span> seconds</p>| until the next download)'
    RECAPTCHA_PATTERN = r'<div id="recaptcha_image" class="pic"></div>'
    ERROR_PATTERN     = r'Wrong Captcha'

    INFO_PATTERN      = r'<div class="name-size">(?P<N>.+?) <small>\((?P<S>[\d.,]+) (?P<U>[\w^_]+)\)</small></div>'
    SIZE_REPLACEMENTS = [('Kb','KB'), ('Mb','MB'), ('Gb','GB')]

    LINK_PATTERN      = r'<div class="premium-download">\s+<a href="(.+?)"'
