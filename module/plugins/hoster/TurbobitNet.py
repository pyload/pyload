# -*- coding: utf-8 -*-

import binascii
import random
import re
import time
import urllib

import Crypto.Cipher.ARC4
import pycurl

from ..captcha.ReCaptcha import ReCaptcha
from ..internal.misc import timestamp
from ..internal.SimpleHoster import SimpleHoster


class TurbobitNet(SimpleHoster):
    __name__ = "TurbobitNet"
    __type__ = "hoster"
    __version__ = "0.32"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.)?turbobit\.net/(?:download/free/)?(?P<ID>\w+)'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool",
                   "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Turbobit.net hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz"),
                   ("prOq", None),
                   ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    URL_REPLACEMENTS = [(__pattern__ + ".*", "https://turbobit.net/\g<ID>.html")]

    COOKIES = [("turbobit.net", "user_lang", "en")]

    LOGIN_PREMIUM = True  #: Free download unsupported

    INFO_PATTERN = r'<title>\s*Download file (?P<N>.+?) \((?P<S>[\d.,]+) (?P<U>[\w^_]+)\)'
    OFFLINE_PATTERN = r'<h2>File Not Found</h2>|html\(\'File (?:was )?not found'
    TEMP_OFFLINE_PATTERN = r''

    LINK_PATTERN = r'<a href=[\'"](.+?/download/redirect/[^"\']+)'

    def handle_premium(self, pyfile):
        m = re.search(self.LINK_PATTERN, self.data)
        if m is not None:
            self.link = m.group(1)
