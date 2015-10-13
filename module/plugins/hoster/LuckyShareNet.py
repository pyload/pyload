# -*- coding: utf-8 -*-

import re

from module.common.json_layer import json_loads
from module.plugins.captcha.ReCaptcha import ReCaptcha
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class LuckyShareNet(SimpleHoster):
    __name__    = "LuckyShareNet"
    __type__    = "hoster"
    __version__ = "0.10"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?luckyshare\.net/(?P<ID>\d{10,})'
    __config__  = [("activated", "bool", "Activated", True),
                   ("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """LuckyShare.net hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it")]


    INFO_PATTERN = r'<h1 class=\'file_name\'>(?P<N>\S+)</h1>\s*<span class=\'file_size\'>Filesize: (?P<S>[\d.,]+)(?P<U>[\w^_]+)</span>'
    OFFLINE_PATTERN = r'There is no such file available'


    def parse_json(self, rep):
        if 'AJAX Error' in rep:
            html = self.load(self.pyfile.url)
            m = re.search(r"waitingtime = (\d+);", html)
            if m is not None:
                seconds = int(m.group(1))
                self.log_debug("You have to wait %d seconds between free downloads" % seconds)
                self.retry(wait=seconds)
            else:
                self.error(_("Unable to detect wait time between free downloads"))
        elif 'Hash expired' in rep:
            self.retry(msg=_("Hash expired"))
        return json_loads(rep)


    #@TODO: There should be a filesize limit for free downloads
    #:       Some files could not be downloaded in free mode
    def handle_free(self, pyfile):
        rep = self.load(r"http://luckyshare.net/download/request/type/time/file/" + self.info['pattern']['ID'])

        self.log_debug("JSON: " + rep)

        json = self.parse_json(rep)
        self.wait(json['time'])

        recaptcha = ReCaptcha(self)

        response, challenge = recaptcha.challenge()
        rep = self.load(r"http://luckyshare.net/download/verify/challenge/%s/response/%s/hash/%s" %
                        (challenge, response, json['hash']))

        self.log_debug("JSON: " + rep)

        if 'Verification failed' in rep:
            self.retry_captcha()

        elif 'link' in rep:
            self.captcha.correct()
            json.update(self.parse_json(rep))
            if json['link']:
                self.link = json['link']


getInfo = create_getInfo(LuckyShareNet)
