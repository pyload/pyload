# -*- coding: utf-8 -*-

import re

from ..internal.XFSHoster import XFSHoster
from ..internal.misc import parse_time

class CosmoboxOrg(XFSHoster):
    __name__ = "CosmoboxOrg"
    __type__ = "hoster"
    __version__ = "0.03"
    __status__ = "testing"

    __pattern__ = r'https?://cosmobox\.org/\w{12}'
    __config__ = [("activated", "bool", "Activated", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int",
                   "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Cosmobox.org hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("OzzieIsaacs", "Ozzie.Fernandez.Isaacs@googlemail.com")]

    PLUGIN_DOMAIN = "cosmobox.org"

    NAME_PATTERN = r"You're downloading: (?P<N>.+?)<"
    SIZE_PATTERN = r'<span class="label label-default">(?P<S>[\d.,]+) (?P<U>[\w^_]+)</span>'
    WAIT_PATTERN = r'<span class="circle"><span class="seconds">(\d+)</span></span>'

    URL_REPLACEMENTS = [(r'^http://', "https://")]

    def handle_free(self, pyfile):
        action, inputs = self.parse_html_form(input_names={'op': re.compile(r'^download')})
        if inputs is None:
            self.fail("Free download form not found")

        inputs['method_free'] = "Free+Download"

        self.data = self.load("https://cosmobox.org/download",
                              post=inputs,
                              ref=self.pyfile.url,
                              redirect=False)

        m = re.search(r'role="alert">You have reached your download limit', self.data)
        if m is not None:
            wait_time = 3*60*60  #: wait 3 hours
            self.wait(wait_time)

        else:
            m = re.search(self.WAIT_PATTERN, self.data)
            if m is not None:
                waitmsg = m.group(1).strip()
                wait_time = parse_time(waitmsg)
                self.wait(wait_time)

        action, inputs = self.parse_html_form(input_names={'op': re.compile(r'^download')})
        self.handle_captcha(inputs)
        self.data = self.download("https://cosmobox.org/download", post=inputs)
