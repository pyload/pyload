# -*- coding: utf-8 -*-

import re

from bottle import json_loads

from pyload.plugins.internal.CaptchaService import ReCaptcha
from pyload.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class LuckyShareNet(SimpleHoster):
    __name__ = "LuckyShareNet"
    __type__ = "hoster"
    __version__ = "0.02"

    __pattern__ = r'https?://(?:www\.)?luckyshare.net/(?P<ID>\d{10,})'

    __description__ = """LuckyShare.net hoster plugin"""
    __author_name__ = "stickell"
    __author_mail__ = "l.stickell@yahoo.it"

    FILE_INFO_PATTERN = r"<h1 class='file_name'>(?P<N>\S+)</h1>\s*<span class='file_size'>Filesize: (?P<S>[\d.]+)(?P<U>\w+)</span>"
    OFFLINE_PATTERN = r'There is no such file available'
    RECAPTCHA_KEY = "6LdivsgSAAAAANWh-d7rPE1mus4yVWuSQIJKIYNw"


    def parseJson(self, rep):
        if 'AJAX Error' in rep:
            html = self.load(self.pyfile.url, decode=True)
            m = re.search(r"waitingtime = (\d+);", html)
            if m:
                waittime = int(m.group(1))
                self.logDebug('You have to wait %d seconds between free downloads' % waittime)
                self.retry(wait_time=waittime)
            else:
                self.parseError('Unable to detect wait time between free downloads')
        elif 'Hash expired' in rep:
            self.retry(reason="Hash expired")
        return json_loads(rep)

    # TODO: There should be a filesize limit for free downloads
    # TODO: Some files could not be downloaded in free mode
    def handleFree(self):
        file_id = re.match(self.__pattern__, self.pyfile.url).group('ID')
        self.logDebug('File ID: ' + file_id)
        rep = self.load(r"http://luckyshare.net/download/request/type/time/file/" + file_id, decode=True)
        self.logDebug('JSON: ' + rep)
        json = self.parseJson(rep)

        self.wait(int(json['time']))

        recaptcha = ReCaptcha(self)
        for _ in xrange(5):
            challenge, response = recaptcha.challenge(self.RECAPTCHA_KEY)
            rep = self.load(r"http://luckyshare.net/download/verify/challenge/%s/response/%s/hash/%s" %
                            (challenge, response, json['hash']), decode=True)
            self.logDebug('JSON: ' + rep)
            if 'link' in rep:
                json.update(self.parseJson(rep))
                self.correctCaptcha()
                break
            elif 'Verification failed' in rep:
                self.logInfo('Wrong captcha')
                self.invalidCaptcha()
            else:
                self.parseError('Unable to get downlaod link')

        if not json['link']:
            self.fail("No Download url retrieved/all captcha attempts failed")

        self.logDebug('Direct URL: ' + json['link'])
        self.download(json['link'])


getInfo = create_getInfo(LuckyShareNet)
