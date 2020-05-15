# -*- coding: utf-8 -*-

import pycurl
import re
import urlparse

from ..captcha.ReCaptcha import ReCaptcha
from ..internal.misc import json, parse_html_tag_attr_value
from ..internal.XFSHoster import XFSHoster


class FilejokerNet(XFSHoster):
    __name__ = "FilejokerNet"
    __type__ = "hoster"
    __version__ = "0.10"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.)?filejoker\.net/(?P<ID>\w{12})'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool", "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Filejoker.net hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    PLUGIN_DOMAIN = "filejoker.net"

    ERROR_PATTERN = r'Wrong Captcha|Session expired'
    PREMIUM_ONLY_PATTERN = 'Free Members can download files no bigger'

    WAIT_PATTERN = r'<span id="count" class="alert-success">([\w ]+?)</span> seconds</p>'
    DL_LIMIT_PATTERN = r'Wait [\w ]+? to download for free.'

    INFO_PATTERN = r'<div class="name-size"><span>(?P<N>.+?)</span> <p>\((?P<S>[\d.,]+) (?P<U>[\w^_]+)\)</p></div>'
    SIZE_REPLACEMENTS = [('Kb', 'KB'), ('Mb', 'MB'), ('Gb', 'GB')]

    LINK_PATTERN = r'<div class="premium-download">\s+<a href="(.+?)"'

    @staticmethod
    def filter_form(tag):
        action = parse_html_tag_attr_value("action", tag)
        return ".js" not in action if action else False

    FORM_PATTERN = filter_form
    FORM_INPUTS_MAP = {'op': re.compile(r'^download')}

    API_URL = "https://filejoker.net/zapi"

    def api_response(self, op, **kwargs):
        args = {'op': op}
        args.update(kwargs)
        return json.loads(self.load(self.API_URL, get=args))

    def handle_captcha(self, inputs):
        m = re.search(r'\$\.post\( "/ddl",\s*\{(.+?) \} \);', self.data)
        if m is not None:
            recaptcha = ReCaptcha(self.pyfile)
            captcha_key = recaptcha.detect_key()
            if captcha_key:
                self.captcha = recaptcha
                response, _ = recaptcha.challenge(captcha_key)

                captcha_inputs = {}
                for _i in m.group(1).split(','):
                    _k, _v = _i.split(':', 1)
                    _k = _k.strip('" ')
                    if "g-recaptcha-response" in _v:
                        _v = response + "1111"

                    captcha_inputs[_k] = _v.strip('" ')

                self.req.http.c.setopt(pycurl.HTTPHEADER, ["X-Requested-With: XMLHttpRequest"])

                html = self.load(urlparse.urljoin(self.pyfile.url, "/ddl"),
                                 post=captcha_inputs)

                self.req.http.c.setopt(pycurl.HTTPHEADER, ["X-Requested-With:"])

                if html == "OK":
                    self.captcha.correct()

                else:
                    self.retry_captcha()

    def handle_premium(self, pyfile):
        res = self.api_response("download1",
                                file_code=self.info['pattern']['ID'],
                                session=self.account.info['data']['session'])

        if 'error' in res:
            if res['error'] == "no file":
                self.offline()

            else:
                self.fail(res['error'])

        pyfile.name = res['file_name']
        pyfile.size = res['file_size']

        res = self.api_response("download2",
                                file_code=self.info['pattern']['ID'],
                                download_id=res['download_id'],
                                session=self.account.info['data']['session'])

        if 'error' in res:
            self.fail(res['error'])

        self.link = res['direct_link']

