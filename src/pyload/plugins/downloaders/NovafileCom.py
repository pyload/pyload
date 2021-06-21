# -*- coding: utf-8 -*-

#
# Test links:
# http://novafile.com/vfun4z6o2cit
# http://novafile.com/s6zrr5wemuz4

from ..base.xfs_downloader import XFSDownloader
from ..anticaptchas.HCaptcha import HCaptcha
from ..helpers import search_pattern
from pyload.core.utils import parse
import re

class NovafileCom(XFSDownloader):
    __name__ = "NovafileCom"
    __type__ = "downloader"
    __version__ = "0.12"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?novafile\.com/\w{12}"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Novafile.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("zoidberg", "zoidberg@mujmail.cz"),
        ("stickell", "l.stickell@yahoo.it"),
    ]

    PLUGIN_DOMAIN = "novafile.com"

    ERROR_PATTERN = r'class="alert.+?alert-separate".*?>\s*(?:<p>)?(.*?)\s*</'
    WAIT_PATTERN = r'<p>Please wait <span id="count".*?>(\d+)</span> seconds</p>'

    LINK_PATTERN = r'<a href="(https://s\d+\.novafile\.com/.*?)" class="btn btn-green">Download File</a>'

    def handle_free(self, pyfile):
        #first handle the captcha
        hcaptcha = HCaptcha(self.pyfile)
        captcha_key = hcaptcha.detect_key()
        if captcha_key is None:
            self.fail(self._("captcha key not found"))
        self.captcha = hcaptcha
        post_data = hcaptcha.challenge(captcha_key)

        # Post post command
        values = re.search(r'"file_id": "(\d+)", rand: "(\w+)"', self.data)
        post = {"op":"captcha1", "file_id": values.group(1), "rand": values.group(2), "g-recaptcha-response":post_data}
        resp = self.load("https://novafile.com/ddl", post=post)
        if resp != "OK":
            self.fail(self._("Post request not accepted"))

        # Wait time
        m = search_pattern(self.WAIT_PATTERN, self.data)
        if m is not None:
            try:
                waitmsg = m.group(1).strip()

            except (AttributeError, IndexError):
                waitmsg = m.group(0).strip()

            wait_time = parse.seconds(waitmsg)
            self.set_wait(wait_time)
            self.wait()

        # Get post data
        action, inputs = self.parse_html_form(
            input_names={"op": re.compile(r"^download")}
        )
        self.log_debug(inputs)

        inputs['h-captcha-response'] = post_data
        inputs['g-recaptcha-response'] = post_data
        self.data = self.load(
            pyfile.url,
            post=inputs,
            ref=self.pyfile.url,
            redirect=False
        )

        m = re.search(self.LINK_FREE_PATTERN, self.data)
        if m is not None:
            self.link = m.group(1)
