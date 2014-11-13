# -*- coding: utf-8 -*-

import re

from module.plugins.internal.XFSHoster import XFSHoster, create_getInfo
from pyload.utils import html_unescape


class RarefileNet(XFSHoster):
    __name__    = "RarefileNet"
    __type__    = "hoster"
    __version__ = "0.06"

    __pattern__ = r'http://(?:www\.)?rarefile\.net/\w{12}'

    __description__ = """Rarefile.net hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    HOSTER_DOMAIN = "rarefile.net"

    NAME_PATTERN = r'<td><font color="red">(?P<N>.*?)</font></td>'
    SIZE_PATTERN = r'<td>Size : (?P<S>.+?)&nbsp;'

    LINK_PATTERN = r'<a href="(?P<link>[^"]+)">(?P=link)</a>'


    def handleCaptcha(self, inputs):
        captcha_div = re.search(r'<b>Enter code.*?<div.*?>(.*?)</div>', self.html, re.S).group(1)
        self.logDebug(captcha_div)
        numerals = re.findall('<span.*?padding-left\s*:\s*(\d+).*?>(\d)</span>', html_unescape(captcha_div))
        inputs['code'] = "".join([a[1] for a in sorted(numerals, key=lambda num: int(num[0]))])
        self.logDebug("CAPTCHA", inputs['code'], numerals)
        return 3


getInfo = create_getInfo(RarefileNet)
