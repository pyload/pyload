# -*- coding: utf-8 -*-

import re

from pyload.plugins.internal.CaptchaService import ReCaptcha
from pyload.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class DateiTo(SimpleHoster):
    __name__ = "DateiTo"
    __type__ = "hoster"
    __version__ = "0.02"

    __pattern__ = r'http://(?:www\.)?datei\.to/datei/(?P<ID>\w+)\.html'

    __description__ = """Datei.to hoster plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"

    FILE_NAME_PATTERN = r'Dateiname:</td>\s*<td colspan="2"><strong>(?P<N>.*?)</'
    FILE_SIZE_PATTERN = r'Dateigr&ouml;&szlig;e:</td>\s*<td colspan="2">(?P<S>.*?)</'
    OFFLINE_PATTERN = r'>Datei wurde nicht gefunden<|>Bitte wähle deine Datei aus... <'
    PARALELL_PATTERN = r'>Du lädst bereits eine Datei herunter<'

    WAIT_PATTERN = r'countdown\({seconds: (\d+)'
    DATA_PATTERN = r'url: "(.*?)", data: "(.*?)",'
    RECAPTCHA_KEY_PATTERN = r'Recaptcha.create\("(.*?)"'


    def handleFree(self):
        url = 'http://datei.to/ajax/download.php'
        data = {'P': 'I', 'ID': self.file_info['ID']}

        recaptcha = ReCaptcha(self)

        for _ in xrange(10):
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
                self.parseError('data')
            url = 'http://datei.to/' + m.group(1)
            data = dict(x.split('=') for x in m.group(2).split('&'))

            if url.endswith('recaptcha.php'):
                m = re.search(self.RECAPTCHA_KEY_PATTERN, self.html)
                recaptcha_key = m.group(1) if m else "6LdBbL8SAAAAAI0vKUo58XRwDd5Tu_Ze1DA7qTao"

                data['recaptcha_challenge_field'], data['recaptcha_response_field'] = recaptcha.challenge(recaptcha_key)

        else:
            self.fail('Too bad...')

        download_url = self.html
        self.logDebug('Download URL', download_url)
        self.download(download_url)

    def checkErrors(self):
        m = re.search(self.PARALELL_PATTERN, self.html)
        if m:
            m = re.search(self.WAIT_PATTERN, self.html)
            wait_time = int(m.group(1)) if m else 30
            self.wait(wait_time + 1, False)
            self.retry()

    def doWait(self):
        m = re.search(self.WAIT_PATTERN, self.html)
        wait_time = int(m.group(1)) if m else 30

        self.load('http://datei.to/ajax/download.php', post={'P': 'Ads'})
        self.wait(wait_time + 1, False)


getInfo = create_getInfo(DateiTo)
