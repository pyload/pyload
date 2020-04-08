# -*- coding: utf-8 -*-

import re
import time

from module.PyFile import PyFile

from ..internal.Account import Account
from ..internal.Captcha import Captcha
from ..internal.misc import parse_html_form


class FshareVn(Account):
    __name__ = "FshareVn"
    __type__ = "account"
    __version__ = "0.24"
    __status__ = "testing"

    __description__ = """Fshare.vn account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz"),
                   ("stickell", "l.stickell@yahoo.it"),
                   ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    VALID_UNTIL_PATTERN = ur'>Hạn dùng:.+?>([\d/]+)</span>'
    LIFETIME_PATTERN = ur'<dt>Lần đăng nhập trước:</dt>\s*<dd>.+?</dd>'
    TRAFFIC_LEFT_PATTERN = ur'>Đã SD: </a>\s*([\d.,]+)(?:([\w^_]+))\s*/\s*([\d.,]+)(?:([\w^_]+))'

    def grab_info(self, user, password, data):
        html = self.load("https://www.fshare.vn")

        m = re.search(self.TRAFFIC_LEFT_PATTERN, html)
        if m is not None:
            trafficleft = (self.parse_traffic(m.group(3), m.group(4)) - self.parse_traffic(m.group(1), m.group(2))) if m else None

        else:
            self.log_error(_("TRAFFIC_LEFT_PATTERN not found"))
            trafficleft = None

        if re.search(self.LIFETIME_PATTERN, html):
            self.log_debug("Lifetime membership detected")
            return {'validuntil': -1,
                    'trafficleft': trafficleft,
                    'premium': True}

        m = re.search(self.VALID_UNTIL_PATTERN, html)
        if m is not None:
            premium = True
            validuntil = time.mktime(time.strptime(m.group(1) + " 23:59:59", '%d/%m/%Y %H:%M:%S'))

        else:
            premium = False
            validuntil = None
            trafficleft = None

        return {'validuntil': validuntil,
                'trafficleft': trafficleft,
                'premium': premium}

    def signin(self, user, password, data):
        html = self.load("https://www.fshare.vn")
        if 'href="/site/logout"' in html:
            self.skip_login()

        # dummy pyfile
        pyfile = PyFile(self.pyload.files, -1, "https://fshare.vn", "https://fshare.vn", 0, 0, "", self.classname, -1, -1)
        pyfile.plugin = self
        self.captcha = Captcha(pyfile)

        for i in range(3):
            url, inputs = parse_html_form('id="form-signup"', html)
            if inputs is None:
                self.fail_login("Login form not found")

            inputs.update({'LoginForm[email]': user,
                           'LoginForm[password]': password,
                           'LoginForm[rememberMe]': 1})

            if 'LoginForm[verifyCode]' in inputs:
                m = re.search(r'src="(/site/captchaV3\?v=[^"]+)"', html)
                if m is None:
                    self.fail_login(_("Captcha pattern not found"))
                inputs['LoginForm[verifyCode]'] = self.captcha.decrypt("https://fshare.vn" + m.group(1),
                                                                       input_type="png")

            html = self.load("https://www.fshare.vn/site/login", post=inputs)

            if u"Kết quả phép tính bên dưới không chính xác!" in html or \
                    u"Bạn đã nhập sai nhiều lần" in html:
                self.captcha.invalid()
                continue

            if u"Đã có lỗi xảy ra, vui lòng thử lại lần nữa." in html:
                self.fail_login()

            if not 'href="/site/logout"' in html:
                if 'id="form-signup"' in html:
                    continue

                else:
                    self.fail_login()

            else:
                if 'LoginForm[verifyCode]' in inputs:
                    self.captcha.correct()
                return

        else:
            self.fail_login()

    """
     @NOTE: below are methods
      necessary for captcha to work with account plugins
    """
    def check_status(self):
        pass

    def retry_captcha(self, attemps=10, wait=1, msg=_("Max captcha retries reached")):
        self.captcha.invalid()
        self.fail_login(msg=_("Invalid captcha"))
