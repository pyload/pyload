# -*- coding: utf-8 -*-

############################################################################
# This program is free software: you can redistribute it and/or modify     #
# it under the terms of the GNU Affero General Public License as           #
# published by the Free Software Foundation, either version 3 of the       #
# License, or (at your option) any later version.                          #
#                                                                          #
# This program is distributed in the hope that it will be useful,          #
# but WITHOUT ANY WARRANTY; without even the implied warranty of           #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            #
# GNU Affero General Public License for more details.                      #
#                                                                          #
# You should have received a copy of the GNU Affero General Public License #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.    #
############################################################################

import re

from module.lib.bottle import json_loads
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo, timestamp
from module.plugins.internal.CaptchaService import ReCaptcha


class FilesmonsterComH(SimpleHoster):
    __name__ = "FilesmonsterComH"
    __type__ = "hoster"
    __pattern__ = r"http://(?:w{3}\.)?filesmonster\.com/+dl/.*"
    __version__ = "0.01"
    __description__ = """Filesmonster.com Hoster Plugin"""
    __author_name__ = ("igel")

    BASE_URL = "http://www.filesmonster.com/"
    RECAPTCHA_KEY_PATTERN = r'"http://api.recaptcha.net/challenge\?k=(.*?)[\&"]'
    WAIT_TIME_PATTERN = r"Please wait\s*<span id='sec'>(\d+)</span>"
    LINK_PATTERN = r"onclick=\"get_link\('(.*?)'\)"
    TEMPORARY_OFFLINE_PATTERN = r"You have started to download"
    NEXT_FILE_WAIT_PATTERN = r"will be available for download in (\d+)"
    WRONG_CAPTCHA_PATTERN = r"<p class=\"error\">Wrong captcha"

    def handleCaptcha(self):
      m = re.search(self.RECAPTCHA_KEY_PATTERN, self.html)
      if m:
        captcha_key = m.group(1)
        self.logDebug('found captcha key ' + captcha_key)

        captcha = ReCaptcha(self)
        for i in range(5):
          challenge, response = captcha.challenge(captcha_key)

          self.html = self.load(self.pyfile.url, cookies=True, post={
            "recaptcha_challenge_field": challenge,
            "recaptcha_response_field": response,
          })

          if self.WRONG_CAPTCHA_PATTERN in self.html:
            self.invalidCaptcha()
            self.logDebug('captcha try %d/5 was invalid' % i)
          else:
            self.correctCaptcha()
            break
        else:
          self.fail("No valid captcha solution received")
      else:
        self.parseError('could not find the captcha key')


    def handleWait(self):
      m = re.search(self.WAIT_TIME_PATTERN, self.html)
      if m:
        self.logDebug('waiting %s seconds' % m.group(1))
        self.setWait(m.group(1))
        self.wait()
      else:
        self.parseError('could not parse the wait time')

    def getLink(self):
      m = re.search(self.LINK_PATTERN, self.html)
      if m:
        self.logDebug('reading JSON data from ' + m.group(1))
        json = json_loads(self.load(self.BASE_URL + m.group(1), decode=True, cookies=True))
        if not json['error']:
          return json['url']
        else:
          self.parseError('unhandled json error: ' + json['error'])
      else:
        self.parseError('could not parse the JSON link')


    def getFileInfo(self):
      m = re.search(self.TEMPORARY_OFFLINE_PATTERN, self.html)
      if m:
        m = re.search(self.NEXT_FILE_WAIT_PATTERN, self.html)
        if m:
          wait_time = 60 * int(m.group(1))
          self.logDebug('need to wait %d sec to download the file' % wait_time)
          # wait time for next file is usually in minutes
          self.setWait(wait_time, reconnect = True)
          self.wait()
          self.retry()
        else:
          self.parseError('error parsing time to wait for the next file')
      else:
        self.logDebug('file can be downloaded')



    def handleFree(self):
      self.html = self.load(self.pyfile.url, decode=True, cookies=True)
      # filesmonster starts off with a captcha, so polite...
      self.handleCaptcha()
      # next, we get to wait
      self.handleWait()
      # and finally, we can get the link
      url = self.getLink()
      self.download(url, disposition=True, cookies=True)




