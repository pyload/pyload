# -*- coding: utf-8 -*-
#
# Note:
#   Right now premium support is not added
#   Thus, any file that require premium support
#   cannot be downloaded. Only the file that is free to
#   download can be downloaded.

import re

from module.common.json_layer import json_loads
from module.plugins.internal.CaptchaService import ReCaptcha
from module.plugins.internal.SimpleHoster import SimpleHoster


class NitroflareCom(SimpleHoster):
    __name__    = "NitroflareCom"
    __type__    = "hoster"
    __version__ = "0.05"

    __pattern__ = r'https?://(?:www\.)?nitroflare\.com/view/(?P<ID>[\w^_]+)'

    __description__ = """Nitroflare.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("sahil", "sahilshekhawat01@gmail.com"),
                       ("Walter Purcaro", "vuolter@gmail.com")]

    # URL_REPLACEMENTS = [("http://", "https://")]

    INFO_PATTERN    = r'title="(?P<N>.+?)".+>(?P<S>[\d.,]+) (?P<U>[\w^_]+)'
    OFFLINE_PATTERN = r'>File doesn\'t exist'

    LINK_FREE_PATTERN = r'(https?://[\w\\-]+\\.nitroflare\\.com/.+?)"'


    def handleFree(self, pyfile):
        file_info = self.load("https://nitroflare.com/api/getDownloadLink",
                              get={'file': self.info['pattern']['ID']})

        self.logDebug(file_info[3:])

        file_info = json_loads(file_info[3:])  #: removing non ascii characters
        if file_info['type'] != "success":
            return

        result = file_info['result']  #: already a dict
        if result['linkType'] != "free":
            return

        # delay      = int(result['delay'])
        captcha_key = result['recaptchaPublic']
        filename    = result['name']
        recaptcha   = ReCaptcha(self)

        # used here to load the cookies which will be required later
        self.load(pyfile.url)
        self.load(pyfile.url, post={'goToFreePage': ""})

        self.html = self.load("http://nitroflare.com/ajax/freeDownload.php",
                              post={'method': "startTimer", 'fileId': self.info['pattern']['ID']})[4:]

        if "This file is available with premium key only" in self.html:
            self.fail("This file is available with premium key only")

        elif "downloading is not possible" in self.html:
            wait_time = re.search("You have to wait (\\d+) minutes to download your next file", self.html)
            if wait_time:
                self.wait(wait_time, True)
            else:
                self.fail("Downloading is not possible")

        else:
            self.logDebug(self.html)

            try:
                js_file   = self.load("http://nitroflare.com/js/downloadFree.js?v=1.0.1")
                var_time  = re.search("var time = (\\d+);", js_file)
                wait_time = int(var_time.groups()[0])

            except Exception:
                wait_time = 60

            self.wait(wait_time)

            challenge, response = recaptcha.challenge(captcha_key)

            self.html = self.load("http://nitroflare.com/ajax/freeDownload.php",
                                  post={'method'                   : "fetchDownload",
                                        'recaptcha_challenge_field': challenge,
                                        'recaptcha_response_field' : response})[3:]

            self.logDebug(self.html)

            if "The captcha wasn't entered correctly" in self.html
                return

            if "You have to fill the captcha" in self.html:
                return

            self.link = re.search(self.LINK_FREE_PATTERN, self.html)
