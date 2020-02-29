# -*- coding: utf-8 -*-

import re

from ..captcha.SolveMedia import SolveMedia
from ..internal.misc import json
from ..internal.SimpleHoster import SimpleHoster


class AlfafileNet(SimpleHoster):
    __name__ = "AlfafileNet"
    __type__ = "hoster"
    __version__ = "0.01"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.)?(alfafile\.net)/file/(?P<ID>\w+)'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool", "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """alfafile.net hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    URL_REPLACEMENTS = [(__pattern__ + ".*", r'https://alfafile.net/file/\g<ID>')]

    NAME_PATTERN = r'<strong id="st_file_name" title="(?P<N>.+?)"'
    SIZE_PATTERN = r'<span class="size">((?P<S>[\d.,]+) (?P<U>[\w^_]+)<'

    DL_LIMIT_PATTERN = r'Try again in (.+?)<'

    def setup(self):
        self.multiDL = self.resume_download = self.premium
        self.chunk_limit = 1  #: Critical problems with more chunks

    def handle_free(self, pyfile):
        json_data = self.load(self.fixurl("/download/start_timer/" + self.info['pattern']['ID']))
        json_data = json.loads(json_data)

        if json_data['show_timer']:
            self.wait(json_data['timer'])

            redirect_url = self.fixurl(json_data['redirect_url'])
            self.data = self.load(redirect_url)

            solvemedia = SolveMedia(self.pyfile)
            captcha_key = solvemedia.detect_key()
            if captcha_key:
                self.captcha = solvemedia
                response, challenge = solvemedia.challenge(captcha_key)

                self.data = self.load(redirect_url,
                                      post={'adcopy_response': response,
                                            'adcopy_challenge': challenge})

                self.log_debug(self.data)

        else:
            self.data = json_data['html']
            self.check_errors()


