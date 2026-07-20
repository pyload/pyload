import urllib.parse

import pycurl

from pyload.core.datatypes.pyfile import PyFile

from ..anticaptchas.Turnstile import Turnstile
from ..base.xfs_account import XFSAccount
from ..helpers import parse_html_form, search_pattern


class DdownloadCom(XFSAccount):
    __name__ = "DdownloadCom"
    __type__ = "account"
    __version__ = "0.11"
    __status__ = "testing"

    __description__ = """Ddownload.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    PLUGIN_DOMAIN = "ddownload.com"
    PLUGIN_URL = "http://ddownload.com"

    PREMIUM_PATTERN = r'<[^<]+ma-ultimate-pill[^>]+>Ultimate<'
    TRAFFIC_LEFT_PATTERN = r'\s*<span id="trafficValue">(?P<S>-?\d+)</span>'
    TRAFFIC_LEFT_UNIT = "MB"
    VALID_UNTIL_PATTERN = r'>Active until\s+([\w ]+[0-9]{4})<'

    def setup(self):
        super(DdownloadCom, self).setup()
        self.req.http.c.setopt(pycurl.USERAGENT, "pyLoad/{}".format(self.pyload.version))

    def parse_traffic(self, size, unit=None):  #: returns bytes
        self.log_debug(f"Size: {size}", f"Unit: {unit or 'N/D'}")
        # to match with ddownload's dashboard value, we need to convert the traffic value in a different way
        return int(int(size) / 1000 * 1024**3)

    def signin(self, user, password, data):
        self.data = self.load(self.LOGIN_URL, cookies=self.COOKIES)

        if search_pattern(self.LOGIN_SKIP_PATTERN, self.data):
            self.skip_login()

        action, inputs = parse_html_form('name="FL"', self.data)
        if not inputs:
            inputs = {"op": "login", "redirect": self.PLUGIN_URL}

        inputs.update({"login": user, "password": password})

        if action:
            url = urllib.parse.urljoin(self.LOGIN_URL, action)
        else:
            url = self.LOGIN_URL

        # dummy pyfile
        pyfile = PyFile(self.pyload.files, -1, self.PLUGIN_URL, self.PLUGIN_URL, 0, 0, "", self.classname, -1, -1)
        pyfile.plugin = self

        self.captcha = Turnstile(pyfile)
        captcha_key = self.captcha.detect_key()
        if captcha_key:
            inputs["cf-turnstile-response"] = self.captcha.challenge(captcha_key)

        self.data = self.load(url, post=inputs, cookies=self.COOKIES)

        self.check_errors()


    """
     @NOTE: below are methods
      necessary for captcha to work with account plugins
    """

    def check_status(self):
        pass

    def retry_captcha(self, attempts=10, wait=1, msg="Max captcha retries reached"):
        self.captcha.invalid()
        self.fail_login(msg=self._("Invalid captcha"))
