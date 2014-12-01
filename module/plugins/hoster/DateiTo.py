# -*- coding: utf-8 -*-

import re

from module.plugins.internal.CaptchaService import ReCaptcha
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class DateiTo(SimpleHoster):
    __name__    = "DateiTo"
    __type__    = "hoster"
    __version__ = "0.05"

    __pattern__ = r'http://(?:www\.)?datei\.to/datei/(?P<ID>\w+)\.html'

    __description__ = """Datei.to hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    NAME_PATTERN = r'Dateiname:</td>\s*<td colspan="2"><strong>(?P<N>.*?)</'
    SIZE_PATTERN = r'Dateigr&ouml;&szlig;e:</td>\s*<td colspan="2">(?P<S>.*?)</'
    OFFLINE_PATTERN = r'>Datei wurde nicht gefunden<|>Bitte wähle deine Datei aus... <'
    PARALELL_PATTERN = r'>Du lädst bereits eine Datei herunter<'

    WAIT_PATTERN = r'countdown\({seconds: (\d+)'
    DATA_PATTERN = r'url: "(.*?)", data: "(.*?)",'


    def handleFree(self):
        url = 'http://datei.to/ajax/download.php'
        data = {'P': 'I', 'ID': self.info['pattern']['ID']}
        recaptcha = ReCaptcha(self)

        for _i in xrange(10):
            self.logDebug("URL", url, "POST", data)
            self.html = self.load(url, post=data)
            self.checkErrors()

            if url.endswith('download.php') and 'P' in data:
                if data['P'] == 'I':
                    self.doWait()

                elif data['P'] == 'IV':
                    break

            m = re.search(self.DATA_PATTERN, self.html)
            if m is None:
                self.error(_("data"))
            url = 'http://datei.to/' + m.group(1)
            data = dict(x.split('=') for x in m.group(2).split('&'))

            if url.endswith('recaptcha.php'):
                data['recaptcha_challenge_field'], data['recaptcha_response_field'] = recaptcha.challenge()
        else:
            self.fail(_("Too bad..."))

        download_url = self.html
        self.download(download_url)


    def checkErrors(self):
        m = re.search(self.PARALELL_PATTERN, self.html)
        if m:
            m = re.search(self.WAIT_PATTERN, self.html)
            wait_time = int(m.group(1)) if m else 30
            self.retry(wait_time=wait_time)


    def doWait(self):
        m = re.search(self.WAIT_PATTERN, self.html)
        wait_time = int(m.group(1)) if m else 30

        self.load('http://datei.to/ajax/download.php', post={'P': 'Ads'})
        self.wait(wait_time, False)


getInfo = create_getInfo(DateiTo)
