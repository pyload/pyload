# -*- coding: utf-8 -*-
"""
    Copyright (C) 2012  pyLoad team
    Copyright (C) 2012  JD-Team support@jdownloader.org

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
import random
from urllib import quote
from binascii import hexlify, unhexlify
from Crypto.Cipher import ARC4

from module.network.RequestFactory import getURL
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo, timestamp
from module.plugins.ReCaptcha import ReCaptcha

from pycurl import HTTPHEADER

class TurbobitNet(SimpleHoster):
    __name__ = "TurbobitNet"
    __type__ = "hoster"
    __pattern__ = r"http://(?:\w*\.)?(turbobit.net|unextfiles.com)/(?:download/free/)?(?P<ID>\w+).*"
    __version__ = "0.07"
    __description__ = """Turbobit.net plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    FILE_INFO_PATTERN = r"<span class='file-icon1[^>]*>(?P<N>[^<]+)</span>\s*\((?P<S>[^\)]+)\)\s*</h1>" #long filenames are shortened
    FILE_NAME_PATTERN = r'<meta name="keywords" content="\s+(?P<N>[^,]+)' #full name but missing on page2
    FILE_OFFLINE_PATTERN = r'<h2>File Not Found</h2>|html\(\'File was not found'
    FILE_URL_REPLACEMENTS = [(r"http://(?:\w*\.)?(turbobit.net|unextfiles.com)/(?:download/free/)?(?P<ID>\w+).*", "http://turbobit.net/\g<ID>.html")]
    SH_COOKIES = [("turbobit.net", "user_lang", "en")]

    CAPTCHA_KEY_PATTERN = r'src="http://api\.recaptcha\.net/challenge\?k=([^"]+)"'
    DOWNLOAD_URL_PATTERN = r'(?P<url>/download/redirect/[^"\']+)'
    LIMIT_WAIT_PATTERN = r'<div id="time-limit-text">\s*.*?<span id=\'timeout\'>(\d+)</span>'
    CAPTCHA_SRC_PATTERN = r'<img alt="Captcha" src="(.*?)"'

    def handleFree(self):
        self.url = "http://turbobit.net/download/free/%s" % self.file_info['ID']
        self.html = self.load(self.url)

        rtUpdate = self.getRtUpdate()

        self.solveCaptcha()
        self.req.http.c.setopt(HTTPHEADER, ["X-Requested-With: XMLHttpRequest"])       
        self.url = self.getDownloadUrl(rtUpdate)

        self.wait()
        self.html = self.load(self.url)
        self.req.http.c.setopt(HTTPHEADER, ["X-Requested-With:"])
        self.downloadFile()

    def solveCaptcha(self):       
        for i in range(5):
            found = re.search(self.LIMIT_WAIT_PATTERN, self.html)
            if found:
                wait_time = int(found.group(1))
                self.setWait(wait_time, wait_time > 60)
                self.wait()
                self.retry()

            action, inputs = self.parseHtmlForm("action='#'")
            if not inputs: self.parseError("captcha form")
            self.logDebug(inputs)

            if inputs['captcha_type'] == 'recaptcha':
                recaptcha = ReCaptcha(self)
                found = re.search(self.CAPTCHA_KEY_PATTERN, self.html)
                captcha_key = found.group(1) if found else '6LcTGLoSAAAAAHCWY9TTIrQfjUlxu6kZlTYP50_c'
                inputs['recaptcha_challenge_field'], inputs['recaptcha_response_field'] = recaptcha.challenge(captcha_key)
            else:
                found = re.search(self.CAPTCHA_SRC_PATTERN, self.html)
                if not found: self.parseError('captcha')
                captcha_url = found.group(1)
                inputs['captcha_response'] = self.decryptCaptcha(captcha_url)

            self.logDebug(inputs)
            self.html = self.load(self.url, post = inputs)

            if not "<div class='download-timer-header'>" in self.html:
                self.invalidCaptcha()
            else:
                self.correctCaptcha()
                break
        else: self.fail("Invalid captcha")

    def getRtUpdate(self):
        rtUpdate = self.getStorage("rtUpdate")
        if not rtUpdate:
            if self.getStorage("version") != self.__version__ or int(self.getStorage("timestamp", 0)) +  86400000 < timestamp(): 
                # that's right, we are even using jdownloader updates
                rtUpdate = getURL("http://update0.jdownloader.org/pluginstuff/tbupdate.js")
                rtUpdate = self.decrypt(rtUpdate.splitlines()[1])
                # but we still need to fix the syntax to work with other engines than rhino                
                rtUpdate = re.sub(r'for each\(var (\w+) in(\[[^\]]+\])\)\{',r'zza=\2;for(var zzi=0;zzi<zza.length;zzi++){\1=zza[zzi];',rtUpdate)
                rtUpdate = re.sub(r"for\((\w+)=",r"for(var \1=", rtUpdate)
                
                self.logDebug("rtUpdate")
                self.setStorage("rtUpdate", rtUpdate)
                self.setStorage("timestamp", timestamp())
                self.setStorage("version", self.__version__)
            else:
                self.logError("Unable to download, wait for update...")
                self.tempOffline()

        return rtUpdate

    def getDownloadUrl(self, rtUpdate):
        self.req.http.lastURL = self.url

        found = re.search("(/\w+/timeout\.js\?\w+=)([^\"\'<>]+)", self.html)
        url = "http://turbobit.net%s%s" % (found.groups() if found else ('/files/timeout.js?ver=', ''.join(random.choice('0123456789ABCDEF') for x in range(32))))
        fun = self.load(url)

        self.setWait(65, False)

        for b in [1,3]:
            self.jscode = "var id = \'%s\';var b = %d;var inn = \'%s\';%sout" % (self.file_info['ID'], b, quote(fun), rtUpdate)
            
            try:
                out = self.js.eval(self.jscode)
                self.logDebug("URL", self.js.engine, out)
                if out.startswith('/download/'):
                    return "http://turbobit.net%s" % out.strip()
            except Exception, e:
                self.logError(e)
        else:
            if self.retries >= 2:
                # retry with updated js
                self.delStorage("rtUpdate")
            self.retry()

    def decrypt(self, data):
        cipher = ARC4.new(hexlify('E\x15\xa1\x9e\xa3M\xa0\xc6\xa0\x84\xb6H\x83\xa8o\xa0'))
        return unhexlify(cipher.encrypt(unhexlify(data)))
    
    def getLocalTimeString():
        lt = time.localtime()
        tz = time.altzone if lt.tm_isdst else time.timezone 
        return "%s GMT%+03d%02d" % (time.strftime("%a %b %d %Y %H:%M:%S", lt), -tz // 3600, tz % 3600)        

    def handlePremium(self):
        self.logDebug("Premium download as user %s" % self.user)
        self.downloadFile()

    def downloadFile(self):
        found = re.search(self.DOWNLOAD_URL_PATTERN, self.html)
        if not found: self.parseError("download link")
        self.url = "http://turbobit.net" + found.group('url')
        self.logDebug(self.url)
        self.download(self.url)

getInfo = create_getInfo(TurbobitNet)