# -*- coding: utf-8 -*-
import re
from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo

class HipfileCom(XFileSharingPro):
    __name__ = "HipfileCom"
    __type__ = "hoster"
    __version__ = "0.1"
    __pattern__ = r'http://(?:www\.)?hipfile\.com/\w{12}'
    __description__ = """hipfile.com hoster plugin"""

    HOSTER_NAME = "hipfile.com"
    FILE_SIZE_PATTERN = r'<tr><td align=right><b>Size:</b></td><td>(?P<S>[0-9\.])+ (?P<U>[kKMG]?B)'
    DIRECT_LINK_PATTERN = r'<a href="(http://\w*\.?hipfile.com[^"]*)" onclick="return btnClick\(\);">'
    WAIT_PATTERN = r'<span id="countdown_str">Wait  <span id="[^"]*">(\d+)</span>'

    def getDownloadLink(self):
        # stage1: press the "Free Download" button
        self.logDebug('stage1')
        data = self.getPostParameters()
        #self.html = self.load(self.pyfile.url, post=data, ref=True, decode=True)

        # stage2: wait some time and press the "Download File" button
        self.logDebug('stage2')
        #data = self.getPostParameters()
        wait_time = re.search(self.WAIT_PATTERN, self.html, re.MULTILINE | re.DOTALL).group(1)
        self.logDebug("hoster told us to wait %s seconds" % wait_time)
        self.wait(wait_time)
        self.html = self.load(self.pyfile.url, post=data, ref=True, decode=True)

        # stage3: get the download link
        return re.search(self.DIRECT_LINK_PATTERN, self.html, re.S).group(1)



getInfo = create_getInfo(HipfileCom)
