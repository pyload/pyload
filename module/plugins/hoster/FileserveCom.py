# -*- coding: utf-8 -*-

import re

from module.common.json_layer import json_loads
from module.network.RequestFactory import getURL
from module.plugins.Hoster import Hoster
from module.plugins.Plugin import chunks
from module.plugins.internal.CaptchaService import ReCaptcha
from module.plugins.internal.SimpleHoster import secondsToMidnight
from module.utils import parseFileSize


def checkFile(plugin, urls):
    html = getURL(plugin.URLS[1], post={"urls": "\n".join(urls)}, decode=True)

    file_info = []
    for li in re.finditer(plugin.LINKCHECK_TR, html, re.S):
        try:
            cols = re.findall(plugin.LINKCHECK_TD, li.group(1))
            if cols:
                file_info.append((
                    cols[1] if cols[1] != '--' else cols[0],
                    parseFileSize(cols[2]) if cols[2] != '--' else 0,
                    2 if cols[3].startswith('Available') else 1,
                    cols[0]))
        except Exception, e:
            continue

    return file_info


class FileserveCom(Hoster):
    __name__    = "FileserveCom"
    __type__    = "hoster"
    __version__ = "0.54"

    __pattern__ = r'http://(?:www\.)?fileserve\.com/file/(?P<ID>[^/]+)'

    __description__ = """Fileserve.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("jeix", "jeix@hasnomail.de"),
                       ("mkaay", "mkaay@mkaay.de"),
                       ("Paul King", None),
                       ("zoidberg", "zoidberg@mujmail.cz")]


    URLS = ["http://www.fileserve.com/file/", "http://www.fileserve.com/link-checker.php",
            "http://www.fileserve.com/checkReCaptcha.php"]
    LINKCHECK_TR = r'<tr>\s*(<td>http://www\.fileserve\.com/file/.*?)</tr>'
    LINKCHECK_TD = r'<td>(?:<[^>]*>|&nbsp;)*([^<]*)'

    CAPTCHA_KEY_PATTERN = r'var reCAPTCHA_publickey=\'(.+?)\''
    LONG_WAIT_PATTERN = r'<li class="title">You need to wait (\d+) (\w+) to start another download\.</li>'
    LINK_EXPIRED_PATTERN = r'Your download link has expired'
    DAILY_LIMIT_PATTERN = r'Your daily download limit has been reached'
    NOT_LOGGED_IN_PATTERN = r'<form (name="loginDialogBoxForm"|id="login_form")|<li><a href="/login\.php">Login</a></li>'


    def setup(self):
        self.resumeDownload = self.multiDL = self.premium
        self.file_id = re.match(self.__pattern__, self.pyfile.url).group('ID')
        self.url     = "%s%s" % (self.URLS[0], self.file_id)

        self.logDebug("File ID: %s URL: %s" % (self.file_id, self.url))


    def process(self, pyfile):
        pyfile.name, pyfile.size, status, self.url = checkFile(self, [self.url])[0]
        if status != 2:
            self.offline()
        self.logDebug("File Name: %s Size: %d" % (pyfile.name, pyfile.size))

        if self.premium:
            self.handlePremium()
        else:
            self.handleFree()


    def handleFree(self):
        self.html = self.load(self.url)
        action = self.load(self.url, post={"checkDownload": "check"}, decode=True)
        action = json_loads(action)
        self.logDebug(action)

        if "fail" in action:
            if action['fail'] == "timeLimit":
                self.html = self.load(self.url, post={"checkDownload": "showError", "errorType": "timeLimit"},
                                      decode=True)

                self.doLongWait(re.search(self.LONG_WAIT_PATTERN, self.html))

            elif action['fail'] == "parallelDownload":
                self.logWarning(_("Parallel download error, now waiting 60s"))
                self.retry(wait_time=60, reason=_("parallelDownload"))

            else:
                self.fail(_("Download check returned: %s") % action['fail'])

        elif "success" in action:
            if action['success'] == "showCaptcha":
                self.doCaptcha()
                self.doTimmer()
            elif action['success'] == "showTimmer":
                self.doTimmer()

        else:
            self.error(_("Unknown server response"))

        # show download link
        res = self.load(self.url, post={"downloadLink": "show"}, decode=True)
        self.logDebug("Show downloadLink response: %s" % res)
        if "fail" in res:
            self.error(_("Couldn't retrieve download url"))

        # this may either download our file or forward us to an error page
        self.download(self.url, post={"download": "normal"})
        self.logDebug(self.req.http.lastEffectiveURL)

        check = self.checkDownload({"expired": self.LINK_EXPIRED_PATTERN,
                                    "wait"   : re.compile(self.LONG_WAIT_PATTERN),
                                    "limit"  : self.DAILY_LIMIT_PATTERN})

        if check == "expired":
            self.logDebug("Download link was expired")
            self.retry()

        elif check == "wait":
            self.doLongWait(self.lastCheck)

        elif check == "limit":
            self.logWarning(_("Download limited reached for today"))
            self.setWait(secondsToMidnight(gmt=2), True)
            self.wait()
            self.retry()

        self.thread.m.reconnecting.wait(3)  # Ease issue with later downloads appearing to be in parallel


    def doTimmer(self):
        res = self.load(self.url, post={"downloadLink": "wait"}, decode=True)
        self.logDebug("Wait response: %s" % res[:80])

        if "fail" in res:
            self.fail(_("Failed getting wait time"))

        if self.__name__ == "FilejungleCom":
            m = re.search(r'"waitTime":(\d+)', res)
            if m is None:
                self.fail(_("Cannot get wait time"))
            wait_time = int(m.group(1))
        else:
            wait_time = int(res) + 3

        self.setWait(wait_time)
        self.wait()


    def doCaptcha(self):
        captcha_key = re.search(self.CAPTCHA_KEY_PATTERN, self.html).group(1)
        recaptcha = ReCaptcha(self)

        for _i in xrange(5):
            response, challenge = recaptcha.challenge(captcha_key)
            res = json_loads(self.load(self.URLS[2],
                                       post={'recaptcha_challenge_field'  : challenge,
                                             'recaptcha_response_field'   : response,
                                             'recaptcha_shortencode_field': self.file_id}))
            if not res['success']:
                self.invalidCaptcha()
            else:
                self.correctCaptcha()
                break
        else:
            self.fail(_("Invalid captcha"))


    def doLongWait(self, m):
        wait_time = (int(m.group(1)) * {'seconds': 1, 'minutes': 60, 'hours': 3600}[m.group(2)]) if m else 12 * 60
        self.setWait(wait_time, True)
        self.wait()
        self.retry()


    def handlePremium(self):
        premium_url = None
        if self.__name__ == "FileserveCom":
            #try api download
            res = self.load("http://app.fileserve.com/api/download/premium/",
                            post={"username": self.user,
                                  "password": self.account.getAccountData(self.user)['password'],
                                  "shorten": self.file_id},
                            decode=True)
            if res:
                res = json_loads(res)
                if res['error_code'] == "302":
                    premium_url = res['next']
                elif res['error_code'] in ["305", "500"]:
                    self.tempOffline()
                elif res['error_code'] in ["403", "605"]:
                    self.resetAccount()
                elif res['error_code'] in ["606", "607", "608"]:
                    self.offline()
                else:
                    self.logError(res['error_code'], res['error_message'])

        self.download(premium_url or self.pyfile.url)

        if not premium_url and self.checkDownload({"login": re.compile(self.NOT_LOGGED_IN_PATTERN)}):
            self.account.relogin(self.user)
            self.retry(reason=_("Not logged in"))


def getInfo(urls):
    for chunk in chunks(urls, 100):
        yield checkFile(FileserveCom, chunk)
