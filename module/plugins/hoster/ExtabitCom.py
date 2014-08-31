# -*- coding: utf-8 -*-

import re

from module.common.json_layer import json_loads

from module.plugins.hoster.UnrestrictLi import secondsToMidnight
from module.plugins.internal.CaptchaService import ReCaptcha
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class ExtabitCom(SimpleHoster):
    __name__ = "ExtabitCom"
    __type__ = "hoster"
    __version__ = "0.6"

    __pattern__ = r'http://(?:www\.)?extabit\.com/(file|go|fid)/(?P<ID>\w+)'

    __description__ = """Extabit.com hoster plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"

    FILE_NAME_PATTERN = r'<th>File:</th>\s*<td class="col-fileinfo">\s*<div title="(?P<N>[^"]+)">'
    FILE_SIZE_PATTERN = r'<th>Size:</th>\s*<td class="col-fileinfo">(?P<S>[^<]+)</td>'
    OFFLINE_PATTERN = r'>File not found<'
    TEMP_OFFLINE_PATTERN = r'>(File is temporary unavailable|No download mirror)<'

    LINK_PATTERN = r'[\'"](http://guest\d+\.extabit\.com/[a-z0-9]+/.*?)[\'"]'


    def handleFree(self):
        if r">Only premium users can download this file" in self.html:
            self.fail("Only premium users can download this file")

        m = re.search(r"Next free download from your ip will be available in <b>(\d+)\s*minutes", self.html)
        if m:
            self.wait(int(m.group(1)) * 60, True)
        elif "The daily downloads limit from your IP is exceeded" in self.html:
            self.logWarning("You have reached your daily downloads limit for today")
            self.wait(secondsToMidnight(gmt=2), True)

        self.logDebug("URL: " + self.req.http.lastEffectiveURL)
        m = re.match(self.__pattern__, self.req.http.lastEffectiveURL)
        fileID = m.group('ID') if m else self.file_info('ID')

        m = re.search(r'recaptcha/api/challenge\?k=(\w+)', self.html)
        if m:
            recaptcha = ReCaptcha(self)
            captcha_key = m.group(1)

            for _ in xrange(5):
                get_data = {"type": "recaptcha"}
                get_data['challenge'], get_data['capture'] = recaptcha.challenge(captcha_key)
                response = json_loads(self.load("http://extabit.com/file/%s/" % fileID, get=get_data))
                if "ok" in response:
                    self.correctCaptcha()
                    break
                else:
                    self.invalidCaptcha()
            else:
                self.fail("Invalid captcha")
        else:
            self.parseError('Captcha')

        if not "href" in response:
            self.parseError('JSON')

        self.html = self.load("http://extabit.com/file/%s%s" % (fileID, response['href']))
        m = re.search(self.LINK_PATTERN, self.html)
        if m is None:
            self.parseError('Download URL')
        url = m.group(1)
        self.logDebug("Download URL: " + url)
        self.download(url)


getInfo = create_getInfo(ExtabitCom)
