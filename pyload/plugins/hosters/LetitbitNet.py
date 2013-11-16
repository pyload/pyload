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

# API Documentation:
# http://api.letitbit.net/reg/static/api.pdf

# Test links (random.bin):
# http://letitbit.net/download/07874.0b5709a7d3beee2408bb1f2eefce/random.bin.html

import re
import urllib

from module.plugins.internal.SimpleHoster import SimpleHoster
from module.common.json_layer import json_loads, json_dumps
from module.plugins.internal.CaptchaService import ReCaptcha


def api_download_info(url):
    json_data = ['yw7XQy2v9', ["download/info", {"link": url}]]
    post_data = urllib.urlencode({'r': json_dumps(json_data)})
    api_rep = urllib.urlopen('http://api.letitbit.net/json', data=post_data).read()
    return json_loads(api_rep)


def getInfo(urls):
    for url in urls:
        api_rep = api_download_info(url)
        if api_rep['status'] == 'OK':
            info = api_rep['data'][0]
            yield (info['name'], info['size'], 2, url)
        else:
            yield (url, 0, 1, url)


class LetitbitNet(SimpleHoster):
    __name__ = "LetitbitNet"
    __type__ = "hoster"
    __pattern__ = r"http://(?:\w*\.)*(letitbit|shareflare).net/download/.*"
    __version__ = "0.23"
    __description__ = """letitbit.net"""
    __author_name__ = ("zoidberg", "z00nx")
    __author_mail__ = ("zoidberg@mujmail.cz", "z00nx0@gmail.com")

    CHECK_URL_PATTERN = r"ajax_check_url\s*=\s*'((http://[^/]+)[^']+)';"
    SECONDS_PATTERN = r"seconds\s*=\s*(\d+);"
    CAPTCHA_CONTROL_FIELD = r"recaptcha_control_field\s=\s'(?P<value>[^']+)'"

    DOMAIN = "http://letitbit.net"
    FILE_URL_REPLACEMENTS = [(r"(?<=http://)([^/]+)", "letitbit.net")]
    RECAPTCHA_KEY = "6Lc9zdMSAAAAAF-7s2wuQ-036pLRbM0p8dDaQdAM"

    def setup(self):
        self.resumeDownload = True
        #TODO confirm that resume works

    def getFileInfo(self):
        api_rep = api_download_info(self.pyfile.url)
        if api_rep['status'] == 'OK':
            self.api_data = api_rep['data'][0]
            self.pyfile.name = self.api_data['name']
            self.pyfile.size = self.api_data['size']
        else:
            self.offline()

    def handleFree(self):
        action, inputs = self.parseHtmlForm('id="ifree_form"')
        if not action:
            self.parseError("page 1 / ifree_form")
        self.pyfile.size = float(inputs['sssize'])
        self.logDebug(action, inputs)
        inputs['desc'] = ""

        self.html = self.load(self.DOMAIN + action, post=inputs, cookies=True)

        # action, inputs = self.parseHtmlForm('id="d3_form"')
        # if not action: self.parseError("page 2 / d3_form")
        # #self.logDebug(action, inputs)
        #
        # self.html = self.load(action, post = inputs, cookies = True)
        #
        # try:
        #     ajax_check_url, captcha_url = re.search(self.CHECK_URL_PATTERN, self.html).groups()
        #     found = re.search(self.SECONDS_PATTERN, self.html)
        #     seconds = int(found.group(1)) if found else 60
        #     self.setWait(seconds+1)
        #     self.wait()
        # except Exception, e:
        #     self.logError(e)
        #     self.parseError("page 3 / js")

        found = re.search(self.SECONDS_PATTERN, self.html)
        seconds = int(found.group(1)) if found else 60
        self.logDebug("Seconds found", seconds)
        found = re.search(self.CAPTCHA_CONTROL_FIELD, self.html)
        recaptcha_control_field = found.group(1)
        self.logDebug("ReCaptcha control field found", recaptcha_control_field)
        self.setWait(seconds + 1)
        self.wait()

        response = self.load("%s/ajax/download3.php" % self.DOMAIN, post=" ", cookies=True)
        if response != '1':
            self.parseError('Unknown response - ajax_check_url')
        self.logDebug(response)

        recaptcha = ReCaptcha(self)
        challenge, response = recaptcha.challenge(self.RECAPTCHA_KEY)
        post_data = {"recaptcha_challenge_field": challenge, "recaptcha_response_field": response,
                     "recaptcha_control_field": recaptcha_control_field}
        self.logDebug("Post data to send", post_data)
        response = self.load('%s/ajax/check_recaptcha.php' % self.DOMAIN, post=post_data, cookies=True)
        self.logDebug(response)
        if not response:
            self.invalidCaptcha()
        if response == "error_free_download_blocked":
            self.logInfo("Daily limit reached, waiting 24 hours")
            self.setWait(24 * 60 * 60)
            self.wait()
        if response == "error_wrong_captcha":
            self.logInfo("Wrong Captcha")
            self.invalidCaptcha()
            self.retry()
        elif response.startswith('['):
            urls = json_loads(response)
        elif response.startswith('http://'):
            urls = [response]
        else:
            self.parseError("Unknown response - captcha check")

        self.correctCaptcha()

        for download_url in urls:
            try:
                self.logDebug("Download URL", download_url)
                self.download(download_url)
                break
            except Exception, e:
                self.logError(e)
        else:
            self.fail("Download did not finish correctly")

    def handlePremium(self):
        api_key = self.user
        premium_key = self.account.getAccountData(self.user)["password"]

        json_data = [api_key, ["download/direct_links", {"pass": premium_key, "link": self.pyfile.url}]]
        api_rep = self.load('http://api.letitbit.net/json', post={'r': json_dumps(json_data)})
        self.logDebug('API Data: ' + api_rep)
        api_rep = json_loads(api_rep)

        if api_rep['status'] == 'FAIL':
            self.fail(api_rep['data'])

        direct_link = api_rep['data'][0][0]
        self.logDebug('Direct Link: ' + direct_link)

        self.download(direct_link, disposition=True)
