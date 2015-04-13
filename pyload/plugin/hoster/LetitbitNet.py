# -*- coding: utf-8 -*-
#
# API Documentation:
# http://api.letitbit.net/reg/static/api.pdf
#
# Test links:
# http://letitbit.net/download/07874.0b5709a7d3beee2408bb1f2eefce/random.bin.html

import re

from urlparse import urljoin

from pyload.utils import json_loads, json_dumps
from pyload.network.RequestFactory import getURL
from pyload.plugin.captcha.ReCaptcha import ReCaptcha
from pyload.plugin.internal.SimpleHoster import SimpleHoster, secondsToMidnight


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
    __name    = "LetitbitNet"
    __type    = "hoster"
    __version = "0.30"

    __pattern = r'https?://(?:www\.)?(letitbit|shareflare)\.net/download/.+'
    __config  = [("use_premium", "bool", "Use premium account if available", True)]

    __description = """Letitbit.net hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("z00nx", "z00nx0@gmail.com")]


    URL_REPLACEMENTS = [(r"(?<=http://)([^/]+)", "letitbit.net")]

    SECONDS_PATTERN = r'seconds\s*=\s*(\d+);'
    CAPTCHA_CONTROL_FIELD = r'recaptcha_control_field\s=\s\'(.+?)\''


    def setup(self):
        self.resumeDownload = True


    def handleFree(self, pyfile):
        action, inputs = self.parseHtmlForm('id="ifree_form"')
        if not action:
            self.error(_("ifree_form"))

        pyfile.size = float(inputs['sssize'])
        self.logDebug(action, inputs)
        inputs['desc'] = ""

        self.html = self.load(urljoin("http://letitbit.net/", action), post=inputs)

        m = re.search(self.SECONDS_PATTERN, self.html)
        seconds = int(m.group(1)) if m else 60

        self.logDebug("Seconds found", seconds)

        m = re.search(self.CAPTCHA_CONTROL_FIELD, self.html)
        recaptcha_control_field = m.group(1)

        self.logDebug("ReCaptcha control field found", recaptcha_control_field)

        self.wait(seconds)

        res = self.load("http://letitbit.net/ajax/download3.php", post=" ")
        if res != '1':
            self.error(_("Unknown response - ajax_check_url"))

        self.logDebug(res)

        recaptcha = ReCaptcha(self)
        response, challenge = recaptcha.challenge()

        post_data = {"recaptcha_challenge_field": challenge,
                     "recaptcha_response_field": response,
                     "recaptcha_control_field": recaptcha_control_field}

        self.logDebug("Post data to send", post_data)

        res = self.load("http://letitbit.net/ajax/check_recaptcha.php", post=post_data)

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

        self.link = urls[0]


    def handlePremium(self, pyfile):
        api_key = self.user
        premium_key = self.account.getAccountData(self.user)['password']

        json_data = [api_key, ["download/direct_links", {"pass": premium_key, "link": pyfile.url}]]
        api_rep = self.load('http://api.letitbit.net/json', post={'r': json_dumps(json_data)})
        self.logDebug("API Data: " + api_rep)
        api_rep = json_loads(api_rep)

        if api_rep['status'] == 'FAIL':
            self.fail(api_rep['data'])

        self.link = api_rep['data'][0][0]
