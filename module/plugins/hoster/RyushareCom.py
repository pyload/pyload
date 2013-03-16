# -*- coding: utf-8 -*-
from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo
import re

class RyushareCom(XFileSharingPro):
    __name__ = "RyushareCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:\w*\.)*?ryushare.com/\w{11,}"
    __version__ = "0.05"
    __description__ = """ryushare.com hoster plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    HOSTER_NAME = "ryushare.com"

    def setup(self):
        self.resumeDownload = self.multiDL = self.premium
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

            # wait 60 seconds
            seconds = re.search(r'(?:You have to|Please) wait (?:<span id="[^"]+">)?(?P<sec>\d+)(?:</span>)? seconds', self.html).group('sec')
            self.setWait(seconds)
            self.wait()

            self.html = self.load(self.pyfile.url, post = inputs)
            if 'Click here to download' in self.html:
                m = re.search(r'<a href="([^"]+)">Click here to download</a>', self.html)
                return m.group(1)

        self.parseError('No direct link within 10 retries')

getInfo = create_getInfo(RyushareCom)
