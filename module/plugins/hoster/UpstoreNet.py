# -*- coding: utf-8 -*-
import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo
from module.plugins.internal.CaptchaService import ReCaptcha


class UpstoreNet(SimpleHoster):
    __name__ = "UpstoreNet"
    __type__ = "hoster"
    __pattern__ = r"https?://(?:www\.)?upstore\.net/"
    __version__ = "0.01"
    __description__ = """Upstore.Net File Download Hoster"""
    __author_name__ = ("igel")

    FILE_INFO_PATTERN = r'<div class="comment">.*?</div>\s*\n<h2 style="margin:0">(?P<N>.*?)</h2>\s*\n<div class="comment">\s*\n\s*(?P<S>[\d.]+) (?P<U>\w+)'
    FILE_OFFLINE_PATTERN = r'<span class="error">File not found</span>'

    WAIT_PATTERN = r"var sec = (\d+)"
    RECAPTCHA_PATTERN = r"Recaptcha.create.*?'(.*?)'"
    CHASH_PATTERN = r'<input type="hidden" name="hash" value="([^"]*)">'
    DIRECT_LINK_PATTERN = r'<a href="(https?://.*?)" target="_blank"><b>'


    def handleFree(self):
        # STAGE 1: get link to continue
        m = re.search(self.CHASH_PATTERN, self.html)
        if not m:
          self.parseError("could not detect hash")
        chash = m.group(1)
        self.logDebug("read hash " + chash)
        # continue to stage2
        post_data = {'hash':chash, 'free': 'Slow download'}
        self.html = self.load(self.pyfile.url, decode=True, post=post_data)


        # try the captcha 5 times
        for i in xrange(5):
          # STAGE 2: solv captcha and wait
          # first get the infos we need: recaptcha key and wait time
          m = re.search(self.RECAPTCHA_PATTERN, self.html)
          if not m:
            self.parseError("could not find recaptcha pattern")
          recaptcha_key = m.group(1)
          self.logDebug("using captcha key " + recaptcha_key)
          recaptcha = ReCaptcha(self)

          m = re.search(self.WAIT_PATTERN, self.html)
          if not m:
            self.parseError("could not find wait pattern")
          wait_time = m.group(1)

          # then, handle the captcha
          challenge, code = recaptcha.challenge(recaptcha_key)
          post_data['recaptcha_challenge_field'] = challenge
          post_data['recaptcha_response_field'] = code

          # then, do the waiting
          self.setWait(wait_time)
          self.wait()

          self.html = self.load(self.pyfile.url, decode=True, post=post_data)

          # STAGE 3: get direct link
          m = re.search(self.DIRECT_LINK_PATTERN, self.html, re.MULTILINE | re.DOTALL)
          if m:
            break

        if not m:
          self.parseError("could not detect direct link")

        direct = m.group(1)
        self.logDebug('found direct link: ' + direct)
        self.download(direct, disposition=True)


getInfo = create_getInfo(UpstoreNet)
