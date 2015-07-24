# -*- coding: utf-8 -*-

import re
import urlparse

from module.plugins.captcha.ReCaptcha import ReCaptcha
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class CrockoCom(SimpleHoster):
    __name__    = "CrockoCom"
    __type__    = "hoster"
    __version__ = "0.21"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?(crocko|easy-share)\.com/\w+'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """Crocko hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    NAME_PATTERN    = r'<span class="fz24">Download:\s*<strong>(?P<N>.*)'
    SIZE_PATTERN    = r'<span class="tip1"><span class="inner">(?P<S>[^<]+)</span></span>'
    OFFLINE_PATTERN = r'<h1>Sorry,<br />the page you\'re looking for <br />isn\'t here.</h1>|File not found'

    CAPTCHA_PATTERN = r"u='(/file_contents/captcha/\w+)';\s*w='(\d+)';"

    FORM_PATTERN = r'<form  method="post" action="(.+?)">(.*?)</form>'
    FORM_INPUT_PATTERN = r'<input[^>]* name="?([^" ]+)"? value="?([^" ]+)"?.*?>'

    NAME_REPLACEMENTS = [(r'<.*?>', '')]


    def handle_free(self, pyfile):
        if "You need Premium membership to download this file." in self.html:
            self.fail(_("You need Premium membership to download this file"))

        for _i in xrange(5):
            m = re.search(self.CAPTCHA_PATTERN, self.html)
            if m:
                url = urlparse.urljoin("http://crocko.com", m.group(1))
                self.wait(m.group(2))
                self.html = self.load(url)
            else:
                break

        m = re.search(self.FORM_PATTERN, self.html, re.S)
        if m is None:
            self.error(_("FORM_PATTERN not found"))

        action, form = m.groups()
        inputs = dict(re.findall(self.FORM_INPUT_PATTERN, form))
        recaptcha = ReCaptcha(self)

        for _i in xrange(5):
            inputs['recaptcha_response_field'], inputs['recaptcha_challenge_field'] = recaptcha.challenge()
            self.download(action, post=inputs)

            if self.check_download({'captcha': recaptcha.KEY_AJAX_PATTERN}):
                self.captcha.invalid()
            else:
                break
        else:
            self.fail(_("No valid captcha solution received"))


getInfo = create_getInfo(CrockoCom)
