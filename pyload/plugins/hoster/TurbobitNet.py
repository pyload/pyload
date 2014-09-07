# -*- coding: utf-8 -*-

import random
import re
import time

from Crypto.Cipher import ARC4
from binascii import hexlify, unhexlify
from pycurl import HTTPHEADER
from urllib import quote

from pyload.network.RequestFactory import getURL
from pyload.plugins.internal.CaptchaService import ReCaptcha
from pyload.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo, timestamp


class TurbobitNet(SimpleHoster):
    __name__ = "TurbobitNet"
    __type__ = "hoster"
    __version__ = "0.11"

    __pattern__ = r'http://(?:www\.)?(turbobit.net|unextfiles.com)/(?!download/folder/)(?:download/free/)?(?P<ID>\w+).*'

    __description__ = """Turbobit.net plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"

    FILE_INFO_PATTERN = r"<span class='file-icon1[^>]*>(?P<N>[^<]+)</span>\s*\((?P<S>[^\)]+)\)\s*</h1>"  #: long filenames are shortened
    FILE_NAME_PATTERN = r'<meta name="keywords" content="\s+(?P<N>[^,]+)'  #: full name but missing on page2
    OFFLINE_PATTERN = r'<h2>File Not Found</h2>|html\(\'File (?:was )?not found'

    FILE_URL_REPLACEMENTS = [(r"http://(?:www\.)?(turbobit.net|unextfiles.com)/(?:download/free/)?(?P<ID>\w+).*",
                              "http://turbobit.net/\g<ID>.html")]
    SH_COOKIES = [(".turbobit.net", "user_lang", "en")]

    LINK_PATTERN = r'(?P<url>/download/redirect/[^"\']+)'
    LIMIT_WAIT_PATTERN = r'<div id="time-limit-text">\s*.*?<span id=\'timeout\'>(\d+)</span>'
    CAPTCHA_KEY_PATTERN = r'src="http://api\.recaptcha\.net/challenge\?k=([^"]+)"'
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
        for _ in xrange(5):
            m = re.search(self.LIMIT_WAIT_PATTERN, self.html)
            if m:
                wait_time = int(m.group(1))
                self.wait(wait_time, wait_time > 60)
                self.retry()

            action, inputs = self.parseHtmlForm("action='#'")
            if not inputs:
                self.parseError("captcha form")
            self.logDebug(inputs)

            if inputs['captcha_type'] == 'recaptcha':
                recaptcha = ReCaptcha(self)
                m = re.search(self.CAPTCHA_KEY_PATTERN, self.html)
                captcha_key = m.group(1) if m else '6LcTGLoSAAAAAHCWY9TTIrQfjUlxu6kZlTYP50_c'
                inputs['recaptcha_challenge_field'], inputs['recaptcha_response_field'] = recaptcha.challenge(
                    captcha_key)
            else:
                m = re.search(self.CAPTCHA_SRC_PATTERN, self.html)
                if m is None:
                    self.parseError('captcha')
                captcha_url = m.group(1)
                inputs['captcha_response'] = self.decryptCaptcha(captcha_url)

            self.logDebug(inputs)
            self.html = self.load(self.url, post=inputs)

            if not "<div class='download-timer-header'>" in self.html:
                self.invalidCaptcha()
            else:
                self.correctCaptcha()
                break
        else:
            self.fail("Invalid captcha")

    def getRtUpdate(self):
        rtUpdate = self.getStorage("rtUpdate")
        if not rtUpdate:
            if self.getStorage("version") != self.__version__ or int(
                    self.getStorage("timestamp", 0)) + 86400000 < timestamp():
                # that's right, we are even using jdownloader updates
                rtUpdate = getURL("http://update0.jdownloader.org/pluginstuff/tbupdate.js")
                rtUpdate = self.decrypt(rtUpdate.splitlines()[1])
                # but we still need to fix the syntax to work with other engines than rhino
                rtUpdate = re.sub(r'for each\(var (\w+) in(\[[^\]]+\])\)\{',
                                  r'zza=\2;for(var zzi=0;zzi<zza.length;zzi++){\1=zza[zzi];', rtUpdate)
                rtUpdate = re.sub(r"for\((\w+)=", r"for(var \1=", rtUpdate)

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

        m = re.search("(/\w+/timeout\.js\?\w+=)([^\"\'<>]+)", self.html)
        url = "http://turbobit.net%s%s" % (m.groups() if m else (
        '/files/timeout.js?ver=', ''.join(random.choice('0123456789ABCDEF') for _ in xrange(32))))
        fun = self.load(url)

        self.setWait(65, False)

        for b in [1, 3]:
            self.jscode = "var id = \'%s\';var b = %d;var inn = \'%s\';%sout" % (
                self.file_info['ID'], b, quote(fun), rtUpdate)

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

    def getLocalTimeString(self):
        lt = time.localtime()
        tz = time.altzone if lt.tm_isdst else time.timezone
        return "%s GMT%+03d%02d" % (time.strftime("%a %b %d %Y %H:%M:%S", lt), -tz // 3600, tz % 3600)

    def handlePremium(self):
        self.logDebug("Premium download as user %s" % self.user)
        self.html = self.load(self.pyfile.url)  # Useless in 0.5
        self.downloadFile()

    def downloadFile(self):
        m = re.search(self.LINK_PATTERN, self.html)
        if m is None:
            self.parseError("download link")
        self.url = "http://turbobit.net" + m.group('url')
        self.logDebug(self.url)
        self.download(self.url)


getInfo = create_getInfo(TurbobitNet)
