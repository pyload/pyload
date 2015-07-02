# -*- coding: utf-8 -*-
import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo
from module.plugins.internal.CaptchaService import ReCaptcha


class UploadableCh(SimpleHoster):
    __name__ = "UploadableCh"
    __type__ = "hoster"
    __pattern__ = r"https?://(?:www\.)?uploadable\.ch/file/(?P<ID>[^/]*)"
    __version__ = "0.01"
    __description__ = """Uploadable.Ch File Download Hoster"""
    __author_name__ = ("igel")

    FILE_INFO_PATTERN = r'<div id="file_name" title=".*?">(?P<N>.*?)<span class="filename_normal">\((?P:<S>[0-9.,]+? (?P<U>\w+?)\)</span></div>'
    FILE_OFFLINE_PATTERN = r'file could not be found'

    WAIT_PATTERN = r'<span class="timer".*?>Wait (\d+) sec'
    WAIT_PENALTY_PATTERN = r'Please wait for (\d+) minutes to download the next file.'
    RECAPTCHA_PATTERN = r"var reCAPTCHA_publickey='(.*?)'"


    def handleCaptcha(self):
        m = re.search(self.RECAPTCHA_PATTERN, self.html)
        if not m:
          self.parseError("could not find recaptcha pattern")
        recaptcha_key = m.group(1)
        self.logDebug("using captcha key " + recaptcha_key)
        recaptcha = ReCaptcha(self)
        return recaptcha.challenge(recaptcha_key)
        
    def handleWait(self):
        m = re.search(self.WAIT_PENALTY_PATTERN, self.html)
        if m:
          mins = m.group(1)
          self.logDebug("Hoster told us to wait %s minutes" % mins)
          self.retry(wait_time = 60 * mins)

    def handleFree(self):
        fid = re.search(self.__pattern__, self.pyfile.url).group('ID')

        # STAGE 1: get captcha challenge & response
        # try the captcha 5 times
        for i in xrange(5):
          challenge, code = self.handleCaptcha()
          post_data['recaptcha_challenge_field'] = challenge
          post_data['recaptcha_response_field'] = code
          post_data['recaptcha_shortencode_field'] = 'PAdc2ZARDzvn'
          post_data['download'] = 'normal'

          # I think waiting is just cient-side
          #self.handleWait()
          self.html = self.load(self.pyfile.url, decode=True, post=post_data)

          # STAGE 2: handle wait penalty time
          self.handleWait()

          # STAGE 3: get direct link
          if self.WRONG_CAPTCHA_PATTERN in self.html:
            self.logDebug("Wrong captcha")
          else:
            self.logDebug('found direct link: ' + direct)
            self.download(self.pyfile.url, decode=True, post={'download':'normal'})
            self.download(direct, disposition=True)
        else:
          self.fail('too many wrong captcha attempts')




getInfo = create_getInfo(UploadableCh)
