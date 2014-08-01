# -*- coding: utf-8 -*-

import re

from module.plugins.internal.CaptchaService import ReCaptcha
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class CrockoCom(SimpleHoster):
    __name__ = "CrockoCom"
    __type__ = "hoster"
    __version__ = "0.16"

    __pattern__ = r'http://(?:www\.)?(crocko|easy-share).com/\w+'

    __description__ = """Crocko hoster plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"

    FILE_NAME_PATTERN = r'<span class="fz24">Download:\s*<strong>(?P<N>.*)'
    FILE_SIZE_PATTERN = r'<span class="tip1"><span class="inner">(?P<S>[^<]+)</span></span>'
    OFFLINE_PATTERN = r"<h1>Sorry,<br />the page you're looking for <br />isn't here.</h1>|File not found"

    CAPTCHA_URL_PATTERN = re.compile(r"u='(/file_contents/captcha/\w+)';\s*w='(\d+)';")
    CAPTCHA_KEY_PATTERN = re.compile(r'Recaptcha.create\("([^"]+)"')

    FORM_PATTERN = r'<form  method="post" action="([^"]+)">(.*?)</form>'
    FORM_INPUT_PATTERN = r'<input[^>]* name="?([^" ]+)"? value="?([^" ]+)"?[^>]*>'

    FILE_NAME_REPLACEMENTS = [(r'<[^>]*>', '')]


    def handleFree(self):
        if "You need Premium membership to download this file." in self.html:
            self.fail("You need Premium membership to download this file.")

        for _ in xrange(5):
            m = re.search(self.CAPTCHA_URL_PATTERN, self.html)
            if m:
                url, wait_time = 'http://crocko.com' + m.group(1), m.group(2)
                self.wait(wait_time)
                self.html = self.load(url)
            else:
                break

        m = re.search(self.CAPTCHA_KEY_PATTERN, self.html)
        if m is None:
            self.parseError('Captcha KEY')
        captcha_key = m.group(1)

        m = re.search(self.FORM_PATTERN, self.html, re.DOTALL)
        if m is None:
            self.parseError('ACTION')
        action, form = m.groups()
        inputs = dict(re.findall(self.FORM_INPUT_PATTERN, form))

        recaptcha = ReCaptcha(self)

        for _ in xrange(5):
            inputs['recaptcha_challenge_field'], inputs['recaptcha_response_field'] = recaptcha.challenge(captcha_key)
            self.download(action, post=inputs)

            check = self.checkDownload({
                "captcha_err": self.CAPTCHA_KEY_PATTERN
            })

            if check == "captcha_err":
                self.invalidCaptcha()
            else:
                break
        else:
            self.fail('No valid captcha solution received')


getInfo = create_getInfo(CrockoCom)
