# -*- coding: utf-8 -*-

import re

from time import sleep

from module.network.HTTPRequest import HTTPRequest
from module.plugins.internal.XFSPHoster import XFSPHoster, create_getInfo


class StreamcloudEu(XFSPHoster):
    __name__ = "StreamcloudEu"
    __type__ = "hoster"
    __version__ = "0.07"

    __pattern__ = r'http://(?:www\.)?streamcloud\.eu/\w{12}'

    __description__ = """Streamcloud.eu hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("seoester", "seoester@googlemail.com")]


    HOSTER_NAME = "streamcloud.eu"

    LINK_PATTERN = r'file: "(http://(stor|cdn)\d+\.streamcloud\.eu:?\d*/.*/video\.(mp4|flv))",'


    def setup(self):
        self.multiDL = True
        self.chunkLimit = 1
        self.resumeDownload = self.premium


    def getDownloadLink(self):
        m = re.search(self.LINK_PATTERN, self.html, re.S)
        if m:
            return m.group(1)

        for i in xrange(5):
            self.logDebug("Getting download link: #%d" % i)
            data = self.getPostParameters()
            httpRequest = HTTPRequest(options=self.req.options)
            httpRequest.cj = self.req.cj
            sleep(10)
            self.html = httpRequest.load(self.pyfile.url, post=data, referer=False, cookies=True, decode=True)
            self.header = httpRequest.header

            m = re.search("Location\s*:\s*(.*)", self.header, re.I)
            if m:
                break

            m = re.search(self.LINK_PATTERN, self.html, re.S)
            if m:
                break

        else:
            if self.errmsg and 'captcha' in self.errmsg:
                self.fail(_("No valid captcha code entered"))
            else:
                self.fail(_("Download link not found"))

        return m.group(1)


    def getPostParameters(self):
        for i in xrange(3):
            if not self.errmsg:
                self.checkErrors()

            if hasattr(self, "FORM_PATTERN"):
                action, inputs = self.parseHtmlForm(self.FORM_PATTERN)
            else:
                action, inputs = self.parseHtmlForm(input_names={"op": re.compile("^download")})

            if not inputs:
                action, inputs = self.parseHtmlForm('F1')
                if not inputs:
                    if self.errmsg:
                        self.retry()
                    else:
                        self.error(_("Form not found"))

            self.logDebug(self.HOSTER_NAME, inputs)

            if 'op' in inputs and inputs['op'] in ("download1", "download2", "download3"):
                if "password" in inputs:
                    if self.passwords:
                        inputs['password'] = self.passwords.pop(0)
                    else:
                        self.fail(_("No or invalid passport"))

                if not self.premium:
                    m = re.search(self.WAIT_PATTERN, self.html)
                    if m:
                        wait_time = int(m.group(1)) + 1
                        self.setWait(wait_time, False)
                    else:
                        wait_time = 0

                    self.captcha = self.handleCaptcha(inputs)

                    if wait_time:
                        self.wait()

                self.errmsg = None
                self.logDebug("getPostParameters {0}".format(i))
                return inputs

            else:
                inputs['referer'] = self.pyfile.url

                if self.premium:
                    inputs['method_premium'] = "Premium Download"
                    if 'method_free' in inputs:
                        del inputs['method_free']
                else:
                    inputs['method_free'] = "Free Download"
                    if 'method_premium' in inputs:
                        del inputs['method_premium']

                self.html = self.load(self.pyfile.url, post=inputs, ref=False)
                self.errmsg = None

        else:
            self.error(_("FORM: %s") % (inputs['op'] if 'op' in inputs else _("UNKNOWN")))


getInfo = create_getInfo(StreamcloudEu)
