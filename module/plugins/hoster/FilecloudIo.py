# -*- coding: utf-8 -*-

import re

from ..captcha.ReCaptcha import ReCaptcha
from ..internal.misc import json
from ..internal.SimpleHoster import SimpleHoster


class FilecloudIo(SimpleHoster):
    __name__ = "FilecloudIo"
    __type__ = "hoster"
    __version__ = "0.16"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.)?(?:filecloud\.io|ifile\.it|mihd\.net)/(?P<ID>\w+)'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool",
                   "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Filecloud.io hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz"),
                   ("stickell", "l.stickell@yahoo.it"),
                   ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    INFO_PATTERN = r'<i class="fa fa-file-archive-o fa-fw"></i>&nbsp;(?P<N>.*?) \[(?P<S>[\d.,]+) (?P<U>[\w^_]+)\]<'
    OFFLINE_PATTERN = r'>The file at this URL was either removed or did not exist in the first place<'
    TEMP_OFFLINE_PATTERN = r'l10n\.FILES__WARNING'

    def setup(self):
        self.resume_download = True
        self.multiDL = True
        self.chunk_limit = 1

    def handle_free(self, pyfile):
        m = re.search(r'__requestUrl\s*=\s*\'(.+)\';', self.data)
        if m is None:
            self.error(_("requestUrl not found"))

        post_url = m.group(1)

        m = re.search(
            r'\$\.ajax\(.*data:\s*(\{.+?\})\s*\}\)\.done\(function', self.data, re.S)
        if m is None:
            self.error(_("post parameters pattern not found"))

        post_data = dict(re.findall(r"'(\w+)'\s*:\s*'(\w+)'", m.group(1)))

        self.captcha = ReCaptcha(pyfile)
        captcha_key = self.captcha.detect_key()
        if captcha_key:
            response, challenge = self.captcha.challenge(captcha_key)
            post_data['r'] = response

        self.data = self.load(post_url, post=post_data)
        json_data = json.loads(self.data)

        if json_data['status'] == "ok":
            self.link = json_data['downloadUrl']

        else:
            self.log_error("Error: %s" % json_data['message'])
            self.fail(json_data['message'])

    def handle_premium(self, pyfile):
        akey = self.account.get_data('akey')
        ukey = self.info['pattern']['ID']
        self.log_debug("Akey: %s | Ukey: %s" % (akey, ukey))
        rep = self.load("http://api.filecloud.io/api-fetch_download_url.api",
                        post={'akey': akey, 'ukey': ukey})
        self.log_debug("FetchDownloadUrl: " + rep)
        rep = json.loads(rep)
        if rep['status'] == "ok":
            self.link = rep['download_url']
        else:
            self.fail(rep['message'])
