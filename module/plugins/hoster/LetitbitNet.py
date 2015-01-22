# -*- coding: utf-8 -*-
#
# API Documentation:
# http://api.letitbit.net/reg/static/api.pdf
#
# Test links:
# http://letitbit.net/download/07874.0b5709a7d3beee2408bb1f2eefce/random.bin.html

import re

from urlparse import urljoin

from module.common.json_layer import json_loads, json_dumps
from module.network.RequestFactory import getURL
from module.plugins.internal.CaptchaService import ReCaptcha
from module.plugins.internal.SimpleHoster import SimpleHoster, secondsToMidnight


def api_response(url):
    json_data = ["yw7XQy2v9", ["download/info", {"link": url}]]
    api_rep   = getURL("http://api.letitbit.net/json",
                       post={'r': json_dumps(json_data)})
    return json_loads(api_rep)


def getInfo(urls):
    for url in urls:
        api_rep = api_response(url)
        if api_rep['status'] == 'OK':
            info = api_rep['data'][0]
            yield (info['name'], info['size'], 2, url)
        else:
            yield (url, 0, 1, url)


class LetitbitNet(SimpleHoster):
    __name__    = "LetitbitNet"
    __type__    = "hoster"
    __version__ = "0.30"

    __pattern__ = r'https?://(?:www\.)?(letitbit|shareflare)\.net/download/.+'

    __description__ = """Letitbit.net hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("z00nx", "z00nx0@gmail.com")]


    URL_REPLACEMENTS = [(r"(?<=http://)([^/]+)", "letitbit.net")]

    SECONDS_PATTERN = r'seconds\s*=\s*(\d+);'
    CAPTCHA_CONTROL_FIELD = r'recaptcha_control_field\s=\s\'(.+?)\''


    def setup(self):
        self.resumeDownload = True


    def getFileInfo(self):
        api_rep = api_response(self.pyfile.url)
        if api_rep['status'] == 'OK':
            self.api_data = api_rep['data'][0]
            self.pyfile.name = self.api_data['name']
            self.pyfile.size = self.api_data['size']
        else:
            self.offline()


    def handleFree(self, pyfile):
        action, inputs = self.parseHtmlForm('id="ifree_form"')
        if not action:
            self.error(_("ifree_form"))

        pyfile.size = float(inputs['sssize'])
        self.logDebug(action, inputs)
        inputs['desc'] = ""

        self.html = self.load(urljoin("http://letitbit.net/", action), post=inputs, cookies=True)

        m = re.search(self.SECONDS_PATTERN, self.html)
        seconds = int(m.group(1)) if m else 60

        self.logDebug("Seconds found", seconds)

        m = re.search(self.CAPTCHA_CONTROL_FIELD, self.html)
        recaptcha_control_field = m.group(1)

        self.logDebug("ReCaptcha control field found", recaptcha_control_field)

        self.wait(seconds)

        res = self.load("http://letitbit.net/ajax/download3.php", post=" ", cookies=True)
        if res != '1':
            self.error(_("Unknown response - ajax_check_url"))

        self.logDebug(res)

        recaptcha = ReCaptcha(self)
        response, challenge = recaptcha.challenge()

        post_data = {"recaptcha_challenge_field": challenge,
                     "recaptcha_response_field": response,
                     "recaptcha_control_field": recaptcha_control_field}

        self.logDebug("Post data to send", post_data)

        res = self.load("http://letitbit.net/ajax/check_recaptcha.php", post=post_data, cookies=True)

        self.logDebug(res)

        if not res:
            self.invalidCaptcha()

        if res == "error_free_download_blocked":
            self.logWarning(_("Daily limit reached"))
            self.wait(secondsToMidnight(gmt=2), True)

        if res == "error_wrong_captcha":
            self.invalidCaptcha()
            self.retry()

        elif res.startswith('['):
            urls = json_loads(res)

        elif res.startswith('http://'):
            urls = [res]

        else:
            self.error(_("Unknown response - captcha check"))

        self.correctCaptcha()

        for download_url in urls:
            try:
                self.download(download_url)
                break
            except Exception, e:
                self.logError(e)
        else:
            self.fail(_("Download did not finish correctly"))


    def handlePremium(self, pyfile):
        api_key = self.user
        premium_key = self.account.getAccountData(self.user)['password']

        json_data = [api_key, ["download/direct_links", {"pass": premium_key, "link": pyfile.url}]]
        api_rep = self.load('http://api.letitbit.net/json', post={'r': json_dumps(json_data)})
        self.logDebug("API Data: " + api_rep)
        api_rep = json_loads(api_rep)

        if api_rep['status'] == 'FAIL':
            self.fail(api_rep['data'])

        self.download(api_rep['data'][0][0], disposition=True)
