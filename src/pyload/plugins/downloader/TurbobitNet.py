# -*- coding: utf-8 -*-

import binascii
import random
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from builtins import range

import js2py
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms

import pycurl

from ..captcha.ReCaptcha import ReCaptcha
from ..base.simple_downloader import SimpleDownloader
from ..utils import timestamp


class TurbobitNet(SimpleDownloader):
    __name__ = "TurbobitNet"
    __type__ = "downloader"
    __version__ = "0.32"
    __status__ = "testing"

    __pyload_version__ = "0.5"

    __pattern__ = r"http://(?:www\.)?turbobit\.net/(?:download/free/)?(?P<ID>\w+)"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Turbobit.net downloader plugin"""
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
            