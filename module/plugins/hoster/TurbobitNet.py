# -*- coding: utf-8 -*-

import binascii
import pycurl
import random
import re
import time
import urllib

from Crypto.Cipher import ARC4

from module.plugins.captcha.ReCaptcha import ReCaptcha
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo, timestamp


class TurbobitNet(SimpleHoster):
    __name__    = "TurbobitNet"
    __type__    = "hoster"
    __version__ = "0.21"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?turbobit\.net/(?:download/free/)?(?P<ID>\w+)'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """Turbobit.net hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("prOq", None)]


    URL_REPLACEMENTS = [(__pattern__ + ".*", "http://turbobit.net/\g<ID>.html")]

    COOKIES = [("turbobit.net", "user_lang", "en")]

    NAME_PATTERN = r'id="file-title">(?P<N>.+?)<'
    SIZE_PATTERN = r'class="file-size">(?P<S>[\d.,]+) (?P<U>[\w^_]+)'
    OFFLINE_PATTERN = r'<h2>File Not Found</h2>|html\(\'File (?:was )?not found'

    LINK_FREE_PATTERN = LINK_PREMIUM_PATTERN = r'(/download/redirect/[^"\']+)'

    LIMIT_WAIT_PATTERN = r'<div id=\'timeout\'>(\d+)<'
    CAPTCHA_PATTERN    = r'<img alt="Captcha" src="(.+?)"'


    def handle_free(self, pyfile):
        self.html = self.load("http://turbobit.net/download/free/%s" % self.info['pattern']['ID'])

        rtUpdate = self.get_rt_update()

        self.solve_captcha()

        self.req.http.c.setopt(pycurl.HTTPHEADER, ["X-Requested-With: XMLHttpRequest"])

        self.html = self.load(self.get_download_url(rtUpdate))

        self.req.http.c.setopt(pycurl.HTTPHEADER, ["X-Requested-With:"])

        m = re.search(self.LINK_FREE_PATTERN, self.html)
        if m:
            self.link = m.group(1)


    def solve_captcha(self):
        for _i in xrange(5):
            m = re.search(self.LIMIT_WAIT_PATTERN, self.html)
            if m:
                wait_time = int(m.group(1))
                self.wait(wait_time, wait_time > 60)
                self.retry()

            action, inputs = self.parse_html_form("action='#'")
            if not inputs:
                self.error(_("Captcha form not found"))
            self.log_debug(inputs)

            if inputs['captcha_type'] == "recaptcha":
                recaptcha = ReCaptcha(self)
                inputs['recaptcha_response_field'], inputs['recaptcha_challenge_field'] = recaptcha.challenge()
            else:
                m = re.search(self.CAPTCHA_PATTERN, self.html)
                if m is None:
                    self.error(_("captcha"))
                captcha_url = m.group(1)
                inputs['captcha_response'] = self.captcha.decrypt(captcha_url)

            self.log_debug(inputs)
            self.html = self.load(self.url, post=inputs)

            if '<div class="captcha-error">Incorrect, try again!<' in self.html:
                self.captcha.invalid()
            else:
                self.captcha.correct()
                break
        else:
            self.fail(_("Invalid captcha"))


    def get_rt_update(self):
        rtUpdate = self.retrieve("rtUpdate")
        if not rtUpdate:
            if self.retrieve("version") is not self.__version__ \
               or int(self.retrieve("timestamp", 0)) + 86400000 < timestamp():
                #: that's right, we are even using jdownloader updates
                rtUpdate = self.load("http://update0.jdownloader.org/pluginstuff/tbupdate.js")
                rtUpdate = self.decrypt(rtUpdate.splitlines()[1])
                #: But we still need to fix the syntax to work with other engines than rhino
                rtUpdate = re.sub(r'for each\(var (\w+) in(\[[^\]]+\])\)\{',
                                  r'zza=\2;for(var zzi=0;zzi<zza.length;zzi++){\1=zza[zzi];', rtUpdate)
                rtUpdate = re.sub(r"for\((\w+)=", r"for(var \1=", rtUpdate)

                self.store("rtUpdate", rtUpdate)
                self.store("timestamp", timestamp())
                self.store("version", self.__version__)
            else:
                self.log_error(_("Unable to download, wait for update..."))
                self.temp_offline()

        return rtUpdate


    def get_download_url(self, rtUpdate):
        self.req.http.lastURL = self.url

        m = re.search("(/\w+/timeout\.js\?\w+=)([^\"\'<>]+)", self.html)
        if m:
            url = "http://turbobit.net%s%s" % m.groups()
        else:
            url = "http://turbobit.net/files/timeout.js?ver=%s" % "".join(random.choice('0123456789ABCDEF') for _i in xrange(32))

        fun = self.load(url)

        self.set_wait(65, False)

        for b in [1, 3]:
            self.jscode = "var id = \'%s\';var b = %d;var inn = \'%s\';%sout" % (
                          self.info['pattern']['ID'], b, urllib.quote(fun), rtUpdate)

            try:
                out = self.js.eval(self.jscode)
                self.log_debug("URL", self.js.engine, out)
                if out.startswith('/download/'):
                    return "http://turbobit.net%s" % out.strip()

            except Exception, e:
                self.log_error(e)
        else:
            if self.retries >= 2:
                #: Retry with updated js
                self.delete("rtUpdate")
            else:
                self.retry()

        self.wait()


    def decrypt(self, data):
        cipher = ARC4.new(binascii.hexlify('E\x15\xa1\x9e\xa3M\xa0\xc6\xa0\x84\xb6H\x83\xa8o\xa0'))
        return binascii.unhexlify(cipher.encrypt(binascii.unhexlify(data)))


    def get_local_time_string(self):
        lt = time.localtime()
        tz = time.altzone if lt.tm_isdst else time.timezone
        return "%s GMT%+03d%02d" % (time.strftime("%a %b %d %Y %H:%M:%S", lt), -tz // 3600, tz % 3600)


getInfo = create_getInfo(TurbobitNet)
