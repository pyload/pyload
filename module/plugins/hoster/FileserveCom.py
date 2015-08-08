# -*- coding: utf-8 -*-

import re

from module.common.json_layer import json_loads
from module.network.RequestFactory import getURL as get_url
from module.plugins.internal.Hoster import Hoster
from module.plugins.internal.Plugin import chunks
from module.plugins.captcha.ReCaptcha import ReCaptcha
from module.plugins.internal.SimpleHoster import seconds_to_midnight
from module.utils import parseFileSize as parse_size


def check_file(plugin, urls):
    html = get_url(plugin.URLS[1], post={'urls': "\n".join(urls)})

    file_info = []
    for li in re.finditer(plugin.LINKCHECK_TR, html, re.S):
        try:
            cols = re.findall(plugin.LINKCHECK_TD, li.group(1))
            if cols:
                file_info.append((
                    cols[1] if cols[1] != '--' else cols[0],
                    parse_size(cols[2]) if cols[2] != '--' else 0,
                    2 if cols[3].startswith('Available') else 1,
                    cols[0]))
        except Exception, e:
            continue

    return file_info


class FileserveCom(Hoster):
    __name__    = "FileserveCom"
    __type__    = "hoster"
    __version__ = "0.58"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?fileserve\.com/file/(?P<ID>[^/]+)'

    __description__ = """Fileserve.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("jeix"     , "jeix@hasnomail.de"  ),
                       ("mkaay"    , "mkaay@mkaay.de"     ),
                       ("Paul King", None                 ),
                       ("zoidberg" , "zoidberg@mujmail.cz")]


    URLS = ["http://www.fileserve.com/file/",
            "http://www.fileserve.com/link-checker.php",
            "http://www.fileserve.com/checkReCaptcha.php"]

    LINKCHECK_TR = r'<tr>\s*(<td>http://www\.fileserve\.com/file/.*?)</tr>'
    LINKCHECK_TD = r'<td>(?:<.*?>|&nbsp;)*([^<]*)'

    CAPTCHA_KEY_PATTERN   = r'var reCAPTCHA_publickey=\'(.+?)\''
    LONG_WAIT_PATTERN     = r'<li class="title">You need to wait (\d+) (\w+) to start another download\.</li>'
    LINK_EXPIRED_PATTERN  = r'Your download link has expired'
    DL_LIMIT_PATTERN      = r'Your daily download limit has been reached'
    NOT_LOGGED_IN_PATTERN = r'<form (name="loginDialogBoxForm"|id="login_form")|<li><a href="/login\.php">Login</a></li>'


    def setup(self):
        self.resume_download = self.multiDL = self.premium
        self.file_id = re.match(self.__pattern__, self.pyfile.url).group('ID')
        self.url     = "%s%s" % (self.URLS[0], self.file_id)

        self.log_debug("File ID: %s URL: %s" % (self.file_id, self.url))


    def process(self, pyfile):
        pyfile.name, pyfile.size, status, self.url = check_file(self, [self.url])[0]
        if status != 2:
            self.offline()
        self.log_debug("File Name: %s Size: %d" % (pyfile.name, pyfile.size))

        if self.premium:
            self.handle_premium()
        else:
            self.handle_free()


    def handle_free(self):
        self.html = self.load(self.url)
        action = self.load(self.url, post={'checkDownload': "check"})
        action = json_loads(action)
        self.log_debug(action)

        if "fail" in action:
            if action['fail'] == "timeLimit":
                self.html = self.load(self.url, post={'checkDownload': "showError", 'errorType': "timeLimit"})

                self.do_long_wait(re.search(self.LONG_WAIT_PATTERN, self.html))

            elif action['fail'] == "parallelDownload":
                self.log_warning(_("Parallel download error, now waiting 60s"))
                self.retry(wait_time=60, reason=_("parallelDownload"))

            else:
                self.fail(_("Download check returned: %s") % action['fail'])

        elif "success" in action:
            if action['success'] == "showCaptcha":
                self.do_captcha()
                self.do_timmer()
            elif action['success'] == "showTimmer":
                self.do_timmer()

        else:
            self.error(_("Unknown server response"))

        #: Show download link
        res = self.load(self.url, post={'downloadLink': "show"})
        self.log_debug("Show downloadLink response: %s" % res)
        if "fail" in res:
            self.error(_("Couldn't retrieve download url"))

        #: This may either download our file or forward us to an error page
        self.download(self.url, post={'download': "normal"})
        self.log_debug(self.req.http.lastEffectiveURL)

        check = self.check_download({'expired': self.LINK_EXPIRED_PATTERN,
                                    'wait'   : re.compile(self.LONG_WAIT_PATTERN),
                                    'limit'  : self.DL_LIMIT_PATTERN})

        if check == "expired":
            self.log_debug("Download link was expired")
            self.retry()

        elif check == "wait":
            self.do_long_wait(self.last_check)

        elif check == "limit":
            self.log_warning(_("Download limited reached for today"))
            self.wait(seconds_to_midnight(gmt=2), True)
            self.retry()

        self.thread.m.reconnecting.wait(3)  #: Ease issue with later downloads appearing to be in parallel


    def do_timmer(self):
        res = self.load(self.url, post={'downloadLink': "wait"})
        self.log_debug("Wait response: %s" % res[:80])

        if "fail" in res:
            self.fail(_("Failed getting wait time"))

        if self.__name__ == "FilejungleCom":
            m = re.search(r'"waitTime":(\d+)', res)
            if m is None:
                self.fail(_("Cannot get wait time"))
            wait_time = int(m.group(1))
        else:
            wait_time = int(res) + 3

        self.wait(wait_time)


    def do_captcha(self):
        captcha_key = re.search(self.CAPTCHA_KEY_PATTERN, self.html).group(1)
        recaptcha = ReCaptcha(self)

        for _i in xrange(5):
            response, challenge = recaptcha.challenge(captcha_key)
            res = json_loads(self.load(self.URLS[2],
                                       post={'recaptcha_challenge_field'  : challenge,
                                             'recaptcha_response_field'   : response,
                                             'recaptcha_shortencode_field': self.file_id}))
            if not res['success']:
                self.captcha.invalid()
            else:
                self.captcha.correct()
                break
        else:
            self.fail(_("Invalid captcha"))


    def do_long_wait(self, m):
        wait_time = (int(m.group(1)) * {'seconds': 1, 'minutes': 60, 'hours': 3600}[m.group(2)]) if m else 12 * 60
        self.wait(wait_time, True)
        self.retry()


    def handle_premium(self):
        premium_url = None
        if self.__name__ == "FileserveCom":
            #: Try api download
            res = self.load("http://app.fileserve.com/api/download/premium/",
                            post={'username': self.user,
                                  'password': self.account.get_info(self.user)['login']['password'],
                                  'shorten': self.file_id})
            if res:
                res = json_loads(res)
                if res['error_code'] == "302":
                    premium_url = res['next']
                elif res['error_code'] in ["305", "500"]:
                    self.temp_offline()
                elif res['error_code'] in ["403", "605"]:
                    self.restart(nopremium=True)
                elif res['error_code'] in ["606", "607", "608"]:
                    self.offline()
                else:
                    self.log_error(res['error_code'], res['error_message'])

        self.download(premium_url or self.pyfile.url)

        if not premium_url and self.check_download({'login': re.compile(self.NOT_LOGGED_IN_PATTERN)}):
            self.account.relogin(self.user)
            self.retry(reason=_("Not logged in"))


def get_info(urls):
    for chunk in chunks(urls, 100):
        yield check_file(FileserveCom, chunk)
