# -*- coding: utf-8 -*-
import re
from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo
from module.utils import html_unescape

class RarefileNet(XFileSharingPro):
    __name__ = "RarefileNet"
    __type__ = "hoster"
    __pattern__ = r"http://(?:\w*\.)*rarefile.net/\w{12}"
    __version__ = "0.01"
    __description__ = """Rarefile.net hoster plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")
    
    FILE_NAME_PATTERN = r'<td><font color="red">(?P<N>.*?)</font></td>'
    FILE_SIZE_PATTERN = r'<td>Size : (?P<S>.+?)&nbsp;'
    
    def handleCaptcha(self, inputs):
        captcha_div = re.search(r'<b>Enter code.*?<div.*?>(.*?)</div>', self.html, re.S).group(1)
        self.logDebug(captcha_div)  
        numerals = re.findall('<span.*?padding-left\s*:\s*(\d+).*?>(\d)</span>', html_unescape(captcha_div))
        inputs['code'] = "".join([a[1] for a in sorted(numerals, key = lambda num: int(num[0]))])
        self.logDebug("CAPTCHA", inputs['code'], numerals) 
        return 3

getInfo = create_getInfo(RarefileNet)