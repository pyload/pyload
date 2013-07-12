# -*- coding: utf-8 -*-
from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo
from module.network.HTTPRequest import HTTPRequest
from time import sleep
import re

class StreamcloudEu(XFileSharingPro):
    __name__ = "StreamcloudEu"
    __type__ = "hoster"
    __pattern__ = r"http://(www\.)?streamcloud\.eu/\S+"
    __version__ = "0.02"
    __description__ = """Streamcloud.eu hoster plugin"""
    __author_name__ = ("seoester")
    __author_mail__ = ("seoester@googlemail.com")

    HOSTER_NAME = "streamcloud.eu"
    DIRECT_LINK_PATTERN = r'file: "(http://(stor|cdn)\d+\.streamcloud.eu:?\d*/.*/video\.mp4)",'

    def setup(self):
        super(StreamcloudEu, self).setup()
        self.multiDL = True

    def getDownloadLink(self):
        found = re.search(self.DIRECT_LINK_PATTERN, self.html, re.S)
        if found:
            return found.group(1)

        for i in range(5):
            self.logDebug("Getting download link: #%d" % i)
            data = self.getPostParameters()
            httpRequest = HTTPRequest(options=self.req.options)
            httpRequest.cj = self.req.cj
            sleep(10)
            self.html = httpRequest.load(self.pyfile.url, post = data, referer=False, cookies=True, decode = True)
            self.header = httpRequest.header

            found = re.search("Location\s*:\s*(.*)", self.header, re.I)
            if found:
                break

            found = re.search(self.DIRECT_LINK_PATTERN, self.html, re.S)
            if found:
                break

        else:
            if self.errmsg and 'captcha' in self.errmsg:
                self.fail("No valid captcha code entered")
            else:
                self.fail("Download link not found")

        return found.group(1)

    def getPostParameters(self):
        for i in range(3):
            if not self.errmsg: self.checkErrors()

            if hasattr(self,"FORM_PATTERN"):
                action, inputs = self.parseHtmlForm(self.FORM_PATTERN)
            else:
                action, inputs = self.parseHtmlForm(input_names={"op": re.compile("^download")})

            if not inputs:
                action, inputs = self.parseHtmlForm('F1')
                if not inputs:
                    if self.errmsg:
                        self.retry()
                    else:
                        self.parseError("Form not found")

            self.logDebug(self.HOSTER_NAME, inputs)

            if 'op' in inputs and inputs['op'] in ('download1', 'download2', 'download3'):
                if "password" in inputs:
                    if self.passwords:
                        inputs['password'] = self.passwords.pop(0)
                    else:
                        self.fail("No or invalid passport")

                if not self.premium:
                    found = re.search(self.WAIT_PATTERN, self.html)
                    if found:
                        wait_time = int(found.group(1)) + 1
                        self.setWait(wait_time, False)
                    else:
                        wait_time = 0

                    self.captcha = self.handleCaptcha(inputs)

                    if wait_time: self.wait()

                self.errmsg = None
                self.logDebug("getPostParameters {0}".format(i))
                return inputs

            else:
                inputs['referer'] = self.pyfile.url

                if self.premium:
                    inputs['method_premium'] = "Premium Download"
                    if 'method_free' in inputs: del inputs['method_free']
                else:
                    inputs['method_free'] = "Free Download"
                    if 'method_premium' in inputs: del inputs['method_premium']

                self.html = self.load(self.pyfile.url, post = inputs, ref = False)
                self.errmsg = None

        else: self.parseError('FORM: %s' % (inputs['op'] if 'op' in inputs else 'UNKNOWN'))


getInfo = create_getInfo(StreamcloudEu)
