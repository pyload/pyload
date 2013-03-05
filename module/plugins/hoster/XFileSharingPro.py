# -*- coding: utf-8 -*-
"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.

    @author: zoidberg
"""

import re
from random import random
from urllib import unquote
from urlparse import urlparse
from pycurl import FOLLOWLOCATION, LOW_SPEED_TIME
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo, PluginParseError
from module.plugins.ReCaptcha import ReCaptcha
from module.plugins.internal.CaptchaService import SolveMedia, AdsCaptcha
from module.utils import html_unescape

class XFileSharingPro(SimpleHoster):
    """
    Common base for XFileSharingPro hosters like EasybytezCom, CramitIn, FiledinoCom...
    Some hosters may work straight away when added to __pattern__
    However, most of them will NOT work because they are either down or running a customized version
    """
    __name__ = "XFileSharingPro"
    __type__ = "hoster"
    __pattern__ = r"^unmatchable$"
    __version__ = "0.17"
    __description__ = """XFileSharingPro common hoster base"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    FILE_NAME_PATTERN = r'<input type="hidden" name="fname" value="(?P<N>[^"]+)"'
    FILE_SIZE_PATTERN = r'You have requested <font color="red">[^<]+</font> \((?P<S>[^<]+)\)</font>'
    FILE_INFO_PATTERN = r'<tr><td align=right><b>Filename:</b></td><td nowrap>(?P<N>[^<]+)</td></tr>\s*.*?<small>\((?P<S>[^<]+)\)</small>'
    FILE_OFFLINE_PATTERN = r'<(b|h[1-6])>File Not Found</(b|h[1-6])>'

    WAIT_PATTERN = r'<span id="countdown_str">.*?>(\d+)</span>'
    LONG_WAIT_PATTERN = r'(?P<H>\d+(?=\s*hour))?.*?(?P<M>\d+(?=\s*minute))?.*?(?P<S>\d+(?=\s*second))?'
    OVR_DOWNLOAD_LINK_PATTERN = r'<h2>Download Link</h2>\s*<textarea[^>]*>([^<]+)'
    OVR_KILL_LINK_PATTERN = r'<h2>Delete Link</h2>\s*<textarea[^>]*>([^<]+)'
    CAPTCHA_URL_PATTERN = r'(http://[^"\']+?/captchas?/[^"\']+)'
    RECAPTCHA_URL_PATTERN = r'http://[^"\']+?recaptcha[^"\']+?\?k=([^"\']+)"'
    CAPTCHA_DIV_PATTERN = r'<b>Enter code.*?<div.*?>(.*?)</div>'
    SOLVEMEDIA_PATTERN = r'http:\/\/api\.solvemedia\.com\/papi\/challenge\.script\?k=(.*?)"'
    ERROR_PATTERN = r'class=["\']err["\'][^>]*>(.*?)</'

    def setup(self):
        if self.__name__ == "XFileSharingPro":
            self.__pattern__ = self.core.pluginManager.hosterPlugins[self.__name__]['pattern']
            self.multiDL = True
        else:
            self.resumeDownload = self.multiDL = self.premium

        self.chunkLimit = 1

    def process(self, pyfile):
        self.prepare()

        if not re.match(self.__pattern__, self.pyfile.url):
            if self.premium:
                self.handleOverriden()
            else:
                self.fail("Only premium users can download from other hosters with %s" % self.HOSTER_NAME)
        else:
            try:
                self.html = self.load(pyfile.url, cookies = False, decode = True)
                self.file_info = self.getFileInfo()
            except PluginParseError:
                self.file_info = None

            self.location = self.getDirectDownloadLink()

            if not self.file_info:
                pyfile.name = html_unescape(unquote(urlparse(self.location if self.location else pyfile.url).path.split("/")[-1]))

            if self.location:
                self.startDownload(self.location)
            elif self.premium:
                self.handlePremium()
            else:
                self.handleFree()

    def prepare(self):
        """ Initialize important variables """
        if not hasattr(self, "HOSTER_NAME"):
            self.HOSTER_NAME = re.search(self.__pattern__, self.pyfile.url).group(1)
        if not hasattr(self, "DIRECT_LINK_PATTERN"):
            self.DIRECT_LINK_PATTERN = r'(http://([^/]*?%s|\d+\.\d+\.\d+\.\d+)(:\d+/d/|/files/\d+/\w+/)[^"\'<]+)' % self.HOSTER_NAME

        self.captcha = self.errmsg = None
        self.passwords = self.getPassword().splitlines()

    def getDirectDownloadLink(self):
        """ Get download link for premium users with direct download enabled """
        self.req.http.lastURL = self.pyfile.url

        self.req.http.c.setopt(FOLLOWLOCATION, 0)
        self.html = self.load(self.pyfile.url, cookies = True, decode = True)
        self.header = self.req.http.header
        self.req.http.c.setopt(FOLLOWLOCATION, 1)

        location = None
        found = re.search("Location\s*:\s*(.*)", self.header, re.I)
        if found and re.match(self.DIRECT_LINK_PATTERN, found.group(1)):
            location = found.group(1).strip()

        return location

    def handleFree(self):
        url = self.getDownloadLink()
        self.logDebug("Download URL: %s" % url)
        self.startDownload(url)

    def getDownloadLink(self):
        for i in range(5):
            self.logDebug("Getting download link: #%d" % i)
            data = self.getPostParameters()

            self.req.http.c.setopt(FOLLOWLOCATION, 0)
            self.html = self.load(self.pyfile.url, post = data, ref = True, decode = True)
            self.header = self.req.http.header
            self.req.http.c.setopt(FOLLOWLOCATION, 1)

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

    def handlePremium(self):
        self.html = self.load(self.pyfile.url, post = self.getPostParameters())
        found = re.search(self.DIRECT_LINK_PATTERN, self.html)
        if not found: self.parseError('DIRECT LINK')
        self.startDownload(found.group(1))

    def handleOverriden(self):
        #only tested with easybytez.com
        self.html = self.load("http://www.%s/" % self.HOSTER_NAME)
        action, inputs =  self.parseHtmlForm('')
        upload_id = "%012d" % int(random()*10**12)
        action += upload_id + "&js_on=1&utype=prem&upload_type=url"
        inputs['tos'] = '1'
        inputs['url_mass'] = self.pyfile.url
        inputs['up1oad_type'] = 'url'

        self.logDebug(self.HOSTER_NAME, action, inputs)
        #wait for file to upload to easybytez.com
        self.req.http.c.setopt(LOW_SPEED_TIME, 600)
        self.html = self.load(action, post = inputs)

        action, inputs = self.parseHtmlForm('F1')
        if not inputs: self.parseError('TEXTAREA')
        self.logDebug(self.HOSTER_NAME, inputs)
        if inputs['st'] == 'OK':
            self.html = self.load(action, post = inputs)
        elif inputs['st'] == 'Can not leech file':
            self.retry(max_tries=20, wait_time=180, reason=inputs['st'])
        else:
            self.fail(inputs['st'])

        #get easybytez.com link for uploaded file
        found = re.search(self.OVR_DOWNLOAD_LINK_PATTERN, self.html)
        if not found: self.parseError('DIRECT LINK (OVR)')
        self.pyfile.url = found.group(1)
        self.retry()

    def startDownload(self, link):
        link = link.strip()
        if self.captcha: self.correctCaptcha()
        self.logDebug('DIRECT LINK: %s' % link)
        self.download(link)

    def checkErrors(self):
        found = re.search(self.ERROR_PATTERN, self.html)
        if found:
            self.errmsg = found.group(1)
            self.logWarning(re.sub(r"<.*?>"," ",self.errmsg))

            if 'wait' in self.errmsg:
                wait_time = sum([int(v) * {"hour": 3600, "minute": 60, "second": 1}[u] for v, u in re.findall('(\d+)\s*(hour|minute|second)?', self.errmsg)])
                self.setWait(wait_time, True)
                self.wait()
            elif 'captcha' in self.errmsg:
                self.invalidCaptcha()
            elif 'premium' in self.errmsg and 'require' in self.errmsg:
                self.fail("File can be downloaded by premium users only")
            elif 'limit' in self.errmsg:
                self.setWait(3600, True)
                self.wait()
                self.retry(25)
            elif 'countdown' in self.errmsg or 'Expired session' in self.errmsg:
                self.retry(3)
            elif 'maintenance' in self.errmsg:
                self.tempOffline()
            elif 'download files up to' in self.errmsg:
                self.fail("File too large for free download")
            else:
                self.fail(self.errmsg)

        else:
            self.errmsg = None

        return self.errmsg

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

            if 'op' in inputs and inputs['op'] in ('download2', 'download3'):
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
                return inputs

            else:
                inputs['referer'] = self.pyfile.url

                if self.premium:
                    inputs['method_premium'] = "Premium Download"
                    if 'method_free' in inputs: del inputs['method_free']
                else:
                    inputs['method_free'] = "Free Download"
                    if 'method_premium' in inputs: del inputs['method_premium']

                self.html = self.load(self.pyfile.url, post = inputs, ref = True)
                self.errmsg = None

        else: self.parseError('FORM: %s' % (inputs['op'] if 'op' in inputs else 'UNKNOWN'))

    def handleCaptcha(self, inputs):
        found = re.search(self.RECAPTCHA_URL_PATTERN, self.html)
        if found:
            recaptcha_key = unquote(found.group(1))
            self.logDebug("RECAPTCHA KEY: %s" % recaptcha_key)
            recaptcha = ReCaptcha(self)
            inputs['recaptcha_challenge_field'], inputs['recaptcha_response_field'] = recaptcha.challenge(recaptcha_key)
            return 1
        else:
            found = re.search(self.CAPTCHA_URL_PATTERN, self.html)
            if found:
                captcha_url = found.group(1)
                inputs['code'] = self.decryptCaptcha(captcha_url)
                return 2
            else:
                found = re.search(self.CAPTCHA_DIV_PATTERN, self.html, re.S)
                if found:
                    captcha_div = found.group(1)
                    self.logDebug(captcha_div)
                    numerals = re.findall('<span.*?padding-left\s*:\s*(\d+).*?>(\d)</span>', html_unescape(captcha_div))
                    inputs['code'] = "".join([a[1] for a in sorted(numerals, key = lambda num: int(num[0]))])
                    self.logDebug("CAPTCHA", inputs['code'], numerals)
                    return 3
                else:
                    found = re.search(self.SOLVEMEDIA_PATTERN, self.html)
                    if found:
                        captcha_key = found.group(1)
                        captcha = SolveMedia(self)
                        inputs['adcopy_challenge'], inputs['adcopy_response'] = captcha.challenge(captcha_key)
                        return 4
        return 0

getInfo = create_getInfo(XFileSharingPro)
