# -*- coding: utf-8 -*-
#
# API Documentation:
# http://api.letitbit.net/reg/static/api.pdf
#
# Test links:
# http://letitbit.net/download/07874.0b5709a7d3beee2408bb1f2eefce/random.bin.html

import re
import urlparse

from module.plugins.internal.utils import json
from module.network.RequestFactory import getURL as get_url
from module.plugins.captcha.ReCaptcha import ReCaptcha
from module.plugins.internal.SimpleHoster import SimpleHoster, seconds_to_midnight


def api_response(url):
    json_data = ["yw7XQy2v9", ["download/info", {'link': url}]]
    api_rep   = get_url("http://api.letitbit.net/json",
                        post={'r': json.dumps(json_data)})
    return json.loads(api_rep)


def get_info(urls):
    for url in urls:
        api_rep = api_response(url)
        if api_rep['status'] == "OK":
            info = api_rep['data'][0]
            yield (info['name'], info['size'], 2, url)
        else:
            yield (url, 0, 1, url)


class LetitbitNet(SimpleHoster):
    __name__    = "LetitbitNet"
    __type__    = "hoster"
    __version__ = "0.35"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?(letitbit|shareflare)\.net/download/.+'
    __config__  = [("activated"   , "bool", "Activated"                                        , True),
                   ("use_premium" , "bool", "Use premium account if available"                 , True),
                   ("fallback"    , "bool", "Fallback to free download if premium fails"       , True),
                   ("chk_filesize", "bool", "Check file size"                                  , True),
                   ("max_wait"    , "int" , "Reconnect if waiting time is greater than minutes", 10  )]

    __description__ = """Letitbit.net hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("z00nx", "z00nx0@gmail.com")]


    URL_REPLACEMENTS = [(r"(?<=http://)([^/]+)", "letitbit.net")]

    SECONDS_PATTERN = r'seconds\s*=\s*(\d+);'
    CAPTCHA_CONTROL_FIELD = r'recaptcha_control_field\s=\s\'(.+?)\''


    def setup(self):
        self.resume_download = True


    def handle_free(self, pyfile):
        action, inputs = self.parse_html_form('id="ifree_form"')
        if not action:
            self.error(_("Form not found"))

        pyfile.size = float(inputs['sssize'])
        self.log_debug(action, inputs)
        inputs['desc'] = ""

        self.data = self.load(urlparse.urljoin("http://letitbit.net/", action), post=inputs)

        m = re.search(self.SECONDS_PATTERN, self.data)
        seconds = int(m.group(1)) if m else 60

        self.log_debug("Seconds found", seconds)

        m = re.search(self.CAPTCHA_CONTROL_FIELD, self.data)
        recaptcha_control_field = m.group(1)

        self.log_debug("ReCaptcha control field found", recaptcha_control_field)

        self.wait(seconds)

        res = self.load("http://letitbit.net/ajax/download3.php", post=" ")
        if res != '1':
            self.error(_("Unknown response - ajax_check_url"))

        self.log_debug(res)

        recaptcha = ReCaptcha(self)
        response, challenge = recaptcha.challenge()

        post_data = {'recaptcha_challenge_field': challenge,
                     'recaptcha_response_field': response,
                     'recaptcha_control_field': recaptcha_control_field}

        self.log_debug("Post data to send", post_data)

        res = self.load("http://letitbit.net/ajax/check_recaptcha.php", post=post_data)

        self.log_debug(res)

        if not res or res == "error_wrong_captcha":
            self.retry_captcha()

        elif res == "error_free_download_blocked":
            self.log_warning(_("Daily limit reached"))
            self.wait(seconds_to_midnight(), True)

        elif res.startswith('['):
            urls = json.loads(res)

        elif res.startswith('http://'):
            urls = [res]

        else:
            self.error(_("Unknown response - captcha check"))

        self.link = urls[0]


    def handle_premium(self, pyfile):
        premium_key = self.account.get_login('password')

        json_data = [self.account.user, ["download/direct_links", {'pass': premium_key, 'link': pyfile.url}]]
        api_rep = self.load('http://api.letitbit.net/json', post={'r': json.dumps(json_data)})
        self.log_debug("API Data: " + api_rep)
        api_rep = json.loads(api_rep)

        if api_rep['status'] == "FAIL":
            self.fail(api_rep['data'])

        self.link = api_rep['data'][0][0]
