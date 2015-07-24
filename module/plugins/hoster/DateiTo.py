# -*- coding: utf-8 -*-

import re

from module.plugins.captcha.ReCaptcha import ReCaptcha
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class DateiTo(SimpleHoster):
    __name__    = "DateiTo"
    __type__    = "hoster"
    __version__ = "0.10"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?datei\.to/datei/(?P<ID>\w+)\.html'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """Datei.to hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    NAME_PATTERN    = r'Dateiname:</td>\s*<td colspan="2"><strong>(?P<N>.*?)</'
    SIZE_PATTERN    = r'Dateigr&ouml;&szlig;e:</td>\s*<td colspan="2">(?P<S>.*?)</'
    OFFLINE_PATTERN = r'>Datei wurde nicht gefunden<|>Bitte wähle deine Datei aus... <'

    WAIT_PATTERN    = r'countdown\({seconds: (\d+)'
    DOWNLOAD_PATTERN = r'>Du lädst bereits eine Datei herunter'

    DATA_PATTERN = r'url: "(.*?)", data: "(.*?)",'


    def handle_free(self, pyfile):
        url = 'http://datei.to/ajax/download.php'
        data = {'P': 'I', 'ID': self.info['pattern']['ID']}
        recaptcha = ReCaptcha(self)

        for _i in xrange(10):
            self.log_debug("URL", url, "POST", data)
            self.html = self.load(url, post=data)
            self.check_errors()

            if url.endswith('download.php') and 'P' in data:
                if data['P'] == "I":
                    self.do_wait()

                elif data['P'] == "IV":
                    break

            m = re.search(self.DATA_PATTERN, self.html)
            if m is None:
                self.error(_("data"))
            url = 'http://datei.to/' + m.group(1)
            data = dict(x.split('=') for x in m.group(2).split('&'))

            if url.endswith('recaptcha.php'):
                data['recaptcha_response_field'], data['recaptcha_challenge_field'] = recaptcha.challenge()
        else:
            self.fail(_("Too bad..."))

        self.link = self.html


    def do_wait(self):
        m = re.search(self.WAIT_PATTERN, self.html)
        wait_time = int(m.group(1)) if m else 30

        self.load('http://datei.to/ajax/download.php', post={'P': 'Ads'})
        self.wait(wait_time, False)


getInfo = create_getInfo(DateiTo)
