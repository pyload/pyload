# -*- coding: utf-8 -*-

import re

from time import sleep

from pycurl import FOLLOWLOCATION

from module.network.HTTPRequest import HTTPRequest
from module.plugins.internal.XFSHoster import XFSHoster, create_getInfo


class StreamcloudEu(XFSHoster):
    __name__    = "StreamcloudEu"
    __type__    = "hoster"
    __version__ = "0.10"

    __pattern__ = r'http://(?:www\.)?streamcloud\.eu/\w{12}'

    __description__ = """Streamcloud.eu hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("seoester", "seoester@googlemail.com")]


    HOSTER_DOMAIN = "streamcloud.eu"

    LINK_PATTERN = r'file: "(http://(stor|cdn)\d+\.streamcloud\.eu:?\d*/.*/video\.(mp4|flv))",'


    def setup(self):
        self.multiDL = True
        self.chunkLimit = 1
        self.resumeDownload = True

    def getDownloadLink(self):
        for i in xrange(1, 5):
            self.logDebug("Getting download link: #%d" % i)

            self.checkErrors()

            m = re.search(self.LINK_PATTERN, self.html, re.S)
            if m:
                break

            data = self.getPostParameters()

            sleep(10)

            self.req.http.c.setopt(FOLLOWLOCATION, 0)

            self.html = self.load(self.pyfile.url, post=data, ref=True, decode=True)
            self.header = self.req.http.header

            self.req.http.c.setopt(FOLLOWLOCATION, 1)

            m = re.search(r'Location\s*:\s*(.*)', self.header, re.I)
            if m:
                break

            m = re.search(self.LINK_PATTERN, self.html, re.S)
            if m:
                break
        else:
            return

        self.errmsg = None

        return m.group(1)


    def getPostParameters(self):
        for _i in xrange(3):
            if hasattr(self, "FORM_PATTERN"):
                action, inputs = self.parseHtmlForm(self.FORM_PATTERN)
            else:
                action, inputs = self.parseHtmlForm(input_names={"op": re.compile("^download")})

            if not inputs:
                action, inputs = self.parseHtmlForm('F1')
                if not inputs:
                    if self.errmsg:
                        self.retry(reason=self.errmsg)
                    else:
                        self.error(_("TEXTAREA F1 not found"))

            self.logDebug(inputs)

            if 'op' in inputs and inputs['op'] in ("download1", "download2", "download3"):
                if "password" in inputs:
                    if self.passwords:
                        inputs['password'] = self.passwords.pop(0)
                    else:
                        self.fail(_("No or invalid passport"))

                if not self.premium:
                    m = re.search(self.WAIT_PATTERN, self.html)
                    if m:
                        wait_time = int(m.group(1))
                        self.setWait(wait_time, False)
                    else:
                        wait_time = 0

                    self.captcha = self.handleCaptcha(inputs)

                    if wait_time:
                        self.wait()

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

                self.html = self.load(self.pyfile.url, post=inputs, ref=True)
        else:
            self.error(_("FORM: %s") % (inputs['op'] if 'op' in inputs else _("UNKNOWN")))

getInfo = create_getInfo(StreamcloudEu)
