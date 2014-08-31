# -*- coding: utf-8 -*-

import re

from module.plugins.internal.CaptchaService import ReCaptcha
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class UpstoreNet(SimpleHoster):
    __name__ = "UpstoreNet"
    __type__ = "hoster"
    __version__ = "0.02"

    __pattern__ = r'https?://(?:www\.)?upstore\.net/'

    __description__ = """Upstore.Net File Download Hoster"""
    __author_name__ = "igel"
    __author_mail__ = "igelkun@myopera.com"

    FILE_INFO_PATTERN = r'<div class="comment">.*?</div>\s*\n<h2 style="margin:0">(?P<N>.*?)</h2>\s*\n<div class="comment">\s*\n\s*(?P<S>[\d.]+) (?P<U>\w+)'
    OFFLINE_PATTERN = r'<span class="error">File not found</span>'

    WAIT_PATTERN = r'var sec = (\d+)'
    CHASH_PATTERN = r'<input type="hidden" name="hash" value="([^"]*)">'
    LINK_PATTERN = r'<a href="(https?://.*?)" target="_blank"><b>'


    def handleFree(self):
        # STAGE 1: get link to continue
        m = re.search(self.CHASH_PATTERN, self.html)
        if m is None:
            self.parseError("could not detect hash")
        chash = m.group(1)
        self.logDebug("read hash " + chash)
        # continue to stage2
        post_data = {'hash': chash, 'free': 'Slow download'}
        self.html = self.load(self.pyfile.url, post=post_data, decode=True)

        # STAGE 2: solv captcha and wait
        # first get the infos we need: recaptcha key and wait time
        recaptcha = ReCaptcha(self)
        if not recaptcha.detect_key(self.html):
            self.parseError("could not find recaptcha pattern")
        self.logDebug("using captcha key " + recaptcha.recaptcha_key)
        # try the captcha 5 times
        for i in xrange(5):
            m = re.search(self.WAIT_PATTERN, self.html)
            if m is None:
                self.parseError("could not find wait pattern")
            wait_time = m.group(1)

            # then, do the waiting
            self.wait(wait_time)

            # then, handle the captcha
            challenge, code = recaptcha.challenge()
            post_data['recaptcha_challenge_field'] = challenge
            post_data['recaptcha_response_field'] = code

            self.html = self.load(self.pyfile.url, post=post_data, decode=True)

            # STAGE 3: get direct link
            m = re.search(self.LINK_PATTERN, self.html, re.DOTALL)
            if m:
                break

        if m is None:
            self.parseError("could not detect direct link")

        direct = m.group(1)
        self.logDebug('found direct link: ' + direct)
        self.download(direct, disposition=True)


getInfo = create_getInfo(UpstoreNet)
