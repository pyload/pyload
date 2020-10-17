# -*- coding: utf-8 -*-
import re

from ..internal.XFSHoster import XFSHoster
from ..internal.misc import search_pattern, parse_time

class UploadshipCom(XFSHoster):
    __name__ = "UploadshipCom"
    __type__ = "hoster"
    __version__ = "0.01"
    __status__ = "testing"

    __pattern__ = r'https://www.uploadship\.com/\w{16}'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool", "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Uploadship.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("OzzieIsaacs", "ozzie.fernandez.isaacs@gmail.com")]

    PLUGIN_DOMAIN = "uploadship.com"

    NAME_PATTERN = r'<span style="display: block; line-height: 17px; word-break: break-all;"><small>(?P<N>.+?)</small></span>'
    SIZE_PATTERN = r'<i class="fa fa-hdd-o" aria-hidden="true"></td><td>((?P<S>[\d.,]+) (?P<U>[\w^_]+)) :'
    WAIT_PATTERN = '<div class="download-timer-seconds">(\d+)</div>'

    FORM_INPUTS_MAP = {'d': re.compile(r'^1')}
    LINK_PATTERN = r'href="(.+?)" target="_blank" class="btn btn-go">Click Here To Download'

    def handle_free(self, pyfile):
        self.check_errors()
        self.data = self.load(pyfile.url)

        action, inputs = self.parse_html_form(self.FORM_PATTERN or "", self.FORM_INPUTS_MAP or {})
                                        # download button id                # download button id
        # https://www.uploadship.com/e5543844e02e54erc3d755cw2522bee5.php?e5543844e02e54erc3d755cw2522bee5=eece12568a839ba4f2fb965e369db4f7

        m = search_pattern(self.WAIT_PATTERN, self.data)
        if m is not None:
            try:
                waitmsg = m.group(1).strip()

            except (AttributeError, IndexError):
                waitmsg = m.group(0).strip()

            wait_time = parse_time(waitmsg)
            self.set_wait(wait_time)
            if wait_time < self.config.get('max_wait', 10) * 60 or \
                    self.pyload.config.get('reconnect', 'activated') is False or \
                    self.pyload.api.isTimeReconnect() is False:
                self.handle_captcha(inputs)
            self.wait()
        else:
            self.handle_captcha(inputs)

        self.data = self.load(pyfile.url,
                              post=inputs, # self._post_parameters(),
                              ref=self.pyfile.url,
                              redirect=False)

        m = search_pattern(self.LINK_PATTERN, self.data, flags=re.M)
        if m is not None:
            self.link = m.group(1)
            return
