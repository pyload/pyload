# -*- coding: utf-8 -*-
from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo
import re


class RyushareCom(XFileSharingPro):
    __name__ = "RyushareCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:\w*\.)*?ryushare.com/\w{11,}"
    __version__ = "0.11"
    __description__ = """ryushare.com hoster plugin"""
    __author_name__ = ("zoidberg", "stickell")
    __author_mail__ = ("zoidberg@mujmail.cz", "l.stickell@yahoo.it")

    HOSTER_NAME = "ryushare.com"

    WAIT_PATTERN = r'(?:You have to|Please) wait (?:(?P<min>\d+) minutes, )?(?:<span id="[^"]+">)?(?P<sec>\d+)(?:</span>)? seconds'
    DIRECT_LINK_PATTERN = r'<a href="([^"]+)">Click here to download</a>'

    def setup(self):
        self.resumeDownload = self.multiDL = True
        if not self.premium:
            self.limitDL = 2
        # Up to 3 chunks allowed in free downloads. Unknown for premium
        self.chunkLimit = 3

    def getDownloadLink(self):
        self.html = self.load(self.pyfile.url)
        action, inputs = self.parseHtmlForm(input_names={"op": re.compile("^download")})
        if inputs.has_key('method_premium'):
            del inputs['method_premium']

        self.html = self.load(self.pyfile.url, post = inputs)
        action, inputs = self.parseHtmlForm('F1')

        for i in xrange(10):
            self.logInfo('Attempt to detect direct link #%d' % i)

            # Wait
            if 'You have reached the download-limit!!!' in self.html:
                self.setWait(3600, True)
            else:
                m = re.search(self.WAIT_PATTERN, self.html).groupdict('0')
                waittime = int(m['min']) * 60 + int(m['sec'])
                self.setWait(waittime)
            self.wait()

            self.html = self.load(self.pyfile.url, post = inputs)
            if 'Click here to download' in self.html:
                m = re.search(self.DIRECT_LINK_PATTERN, self.html)
                return m.group(1)

        self.parseError('No direct link within 10 retries')

getInfo = create_getInfo(RyushareCom)
