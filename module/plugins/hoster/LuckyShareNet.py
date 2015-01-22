# -*- coding: utf-8 -*-

import re

from bottle import json_loads

from module.plugins.internal.CaptchaService import ReCaptcha
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class LuckyShareNet(SimpleHoster):
    __name__    = "LuckyShareNet"
    __type__    = "hoster"
    __version__ = "0.06"

    __pattern__ = r'https?://(?:www\.)?luckyshare\.net/(?P<ID>\d{10,})'

    __description__ = """LuckyShare.net hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it")]


    INFO_PATTERN = r'<h1 class=\'file_name\'>(?P<N>\S+)</h1>\s*<span class=\'file_size\'>Filesize: (?P<S>[\d.,]+)(?P<U>[\w^_]+)</span>'
    OFFLINE_PATTERN = r'There is no such file available'


    def parseJson(self, rep):
        if 'AJAX Error' in rep:
            html = self.load(self.pyfile.url, decode=True)
            m = re.search(r"waitingtime = (\d+);", html)
            if m:
                seconds = int(m.group(1))
                self.logDebug("You have to wait %d seconds between free downloads" % seconds)
                self.retry(wait_time=seconds)
            else:
                self.error(_("Unable to detect wait time between free downloads"))
        elif 'Hash expired' in rep:
            self.retry(reason=_("Hash expired"))
        return json_loads(rep)


    # TODO: There should be a filesize limit for free downloads
    # TODO: Some files could not be downloaded in free mode
    def handleFree(self, pyfile):
        rep = self.load(r"http://luckyshare.net/download/request/type/time/file/" + self.info['pattern']['ID'], decode=True)

        self.logDebug("JSON: " + rep)

        json = self.parseJson(rep)
        self.wait(int(json['time']))

        recaptcha = ReCaptcha(self)

        for _i in xrange(5):
            response, challenge = recaptcha.challenge()
            rep = self.load(r"http://luckyshare.net/download/verify/challenge/%s/response/%s/hash/%s" %
                            (challenge, response, json['hash']), decode=True)
            self.logDebug("JSON: " + rep)
            if 'link' in rep:
                json.update(self.parseJson(rep))
                self.correctCaptcha()
                break
            elif 'Verification failed' in rep:
                self.invalidCaptcha()
            else:
                self.error(_("Unable to get downlaod link"))

        if not json['link']:
            self.fail(_("No Download url retrieved/all captcha attempts failed"))

        self.download(json['link'])


getInfo = create_getInfo(LuckyShareNet)
