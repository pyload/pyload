# -*- coding: utf-8 -*-

import re

from ..captcha.ReCaptcha import ReCaptcha
from ..internal.misc import json, seconds_to_midnight
from ..internal.SimpleHoster import SimpleHoster


class ExtabitCom(SimpleHoster):
    __name__ = "ExtabitCom"
    __type__ = "hoster"
    __version__ = "0.73"
    __status__ = "testing"

    __pattern__ = r'http://(?:www\.)?extabit\.com/(file|go|fid)/(?P<ID>\w+)'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool",
                   "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Extabit.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]

    NAME_PATTERN = r'<th>File:</th>\s*<td class="col-fileinfo">\s*<div title="(?P<N>.+?)">'
    SIZE_PATTERN = r'<th>Size:</th>\s*<td class="col-fileinfo">(?P<S>.+?)</td>'
    OFFLINE_PATTERN = r'>File not found<'
    TEMP_OFFLINE_PATTERN = r'>(File is temporary unavailable|No download mirror)<'

    LINK_FREE_PATTERN = r'[\'"](http://guest\d+\.extabit\.com/\w+/.*?)[\'"]'

    def handle_free(self, pyfile):
        if r'>Only premium users can download this file' in self.data:
            self.fail(_("Only premium users can download this file"))

        m = re.search(
            r'Next free download from your ip will be available in <b>(\d+)\s*minutes',
            self.data)
        if m is not None:
            self.wait(int(m.group(1)) * 60, True)
        elif "The daily downloads limit from your IP is exceeded" in self.data:
            self.log_warning(
                _("You have reached your daily downloads limit for today"))
            self.wait(seconds_to_midnight(), True)

        self.log_debug("URL: " + self.req.http.lastEffectiveURL)
        m = re.match(self.__pattern__, self.req.http.lastEffectiveURL)
        fileID = m.group('ID') if m else self.info['pattern']['ID']

        m = re.search(r'recaptcha/api/challenge\?k=(\w+)', self.data)
        if m is not None:
            self.captcha = ReCaptcha(pyfile)
            captcha_key = m.group(1)

            get_data = {'type': "recaptcha"}
            get_data['capture'], get_data[
                'challenge'] = self.captcha.challenge(captcha_key)

            html = self.load(
                "http://extabit.com/file/%s/" %
                fileID, get=get_data)
            res = json.loads(html)

            if "ok" in res:
                self.captcha.correct()
            else:
                self.retry_captcha()
        else:
            self.error(_("Captcha"))

        if not "href" in res:
            self.error(_("Bad JSON response"))

        self.data = self.load(
            "http://extabit.com/file/%s%s" %
            (fileID, res['href']))

        m = re.search(self.LINK_FREE_PATTERN, self.data)
        if m is None:
            self.error(_("LINK_FREE_PATTERN not found"))

        self.link = m.group(1)
