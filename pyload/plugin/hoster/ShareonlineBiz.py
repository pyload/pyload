# -*- coding: utf-8 -*-

import re

from time import time
from urllib import unquote
from urlparse import urlparse

from pyload.network.RequestFactory import getURL
from pyload.plugin.captcha import ReCaptcha
from pyload.plugin.internal.SimpleHoster import SimpleHoster, create_getInfo


class ShareonlineBiz(SimpleHoster):
    __name    = "ShareonlineBiz"
    __type    = "hoster"
    __version = "0.44"

    __pattern = r'https?://(?:www\.)?(share-online\.biz|egoshare\.com)/(download\.php\?id=|dl/)(?P<ID>\w+)'

    __description = """Shareonline.biz hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("spoob", "spoob@pyload.org"),
                       ("mkaay", "mkaay@mkaay.de"),
                       ("zoidberg", "zoidberg@mujmail.cz"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    URL_REPLACEMENTS = [(__pattern + ".*", "http://www.share-online.biz/dl/\g<ID>")]

    RECAPTCHA_KEY = "6LdatrsSAAAAAHZrB70txiV5p-8Iv8BtVxlTtjKX"

    ERROR_INFO_PATTERN = r'<p class="b">Information:</p>\s*<div>\s*<strong>(.*?)</strong>'


    @classmethod
    def getInfo(cls, url="", html=""):
        info = {'name': urlparse(unquote(url)).path.split('/')[-1] or _("Unknown"), 'size': 0, 'status': 3 if url else 1, 'url': url}

        if url:
            info['pattern'] = re.match(cls.__pattern, url).groupdict()

            field = getURL("http://api.share-online.biz/linkcheck.php",
                           get={'md5': "1"},
                           post={'links': info['pattern']['ID']},
                           decode=True).split(";")

            if field[1] == "OK":
                info['fileid']   = field[0]
                info['status']   = 2
                info['name'] = field[2]
                info['size']     = field[3]  #: in bytes
                info['md5']      = field[4].strip().lower().replace("\n\n", "")  #: md5

            elif field[1] in ("DELETED", "NOT FOUND"):
                info['status'] = 1

        return info


    def setup(self):
        self.resumeDownload = self.premium
        self.multiDL        = False


    def handleCaptcha(self):
        recaptcha = ReCaptcha(self)

        for _i in xrange(5):
            challenge, response = recaptcha.challenge(self.RECAPTCHA_KEY)

            m = re.search(r'var wait=(\d+);', self.html)
            self.setWait(int(m.group(1)) if m else 30)

            res = self.load("%s/free/captcha/%d" % (self.pyfile.url, int(time() * 1000)),
                            post={'dl_free'                  : "1",
                                  'recaptcha_challenge_field': challenge,
                                  'recaptcha_response_field' : response})
            if not res == '0':
                self.correctCaptcha()
                return res
            else:
                self.invalidCaptcha()
        else:
            self.invalidCaptcha()
            self.fail(_("No valid captcha solution received"))


    def handleFree(self):
        self.html = self.load(self.pyfile.url, cookies=True)  #: refer, stuff

        self.wait(3)

        self.html = self.load("%s/free/" % self.pyfile.url, post={"dl_free": "1", "choice": "free"}, decode=True)

        self.checkErrors()

        res = self.handleCaptcha()

        download_url = res.decode("base64")

        if not download_url.startswith("http://"):
            self.error(_("Wrong download url"))

        self.wait()

        self.download(download_url)


    def checkFile(self):
        # check download
        check = self.checkDownload({
            'empty' : re.compile(r"^$"),
            'cookie': re.compile(r'<div id="dl_failure"'),
            'fail'  : re.compile(r"<title>Share-Online")
        })

        if check == "empty":
            self.fail(_("Empty file"))

        elif check == "cookie":
            self.invalidCaptcha()
            self.retry(5, 60, _("Cookie failure"))

        elif check == "fail":
            self.invalidCaptcha()
            self.retry(5, 5 * 60, _("Download failed"))


    def handlePremium(self):  #: should be working better loading (account) api internally
        self.account.getAccountInfo(self.user, True)

        html = self.load("http://api.share-online.biz/account.php",
                        {"username": self.user, "password": self.account.accounts[self.user]['password'],
                         "act": "download", "lid": self.info['fileid']})

        self.api_data = dlinfo = {}

        for line in html.splitlines():
            key, value = line.split(": ")
            dlinfo[key.lower()] = value

        self.logDebug(dlinfo)

        if not dlinfo['status'] == "online":
            self.offline()
        else:
            self.pyfile.name = dlinfo['name']
            self.pyfile.size = int(dlinfo['size'])

            dlLink = dlinfo['url']

            if dlLink == "server_under_maintenance":
                self.tempOffline()
            else:
                self.multiDL = True
                self.download(dlLink)


    def checkErrors(self):
        m = re.search(r"/failure/(.*?)/1", self.req.lastEffectiveURL)
        if m is None:
            self.info.pop('error', None)
            return

        errmsg = m.group(1).lower()

        try:
            self.logError(errmsg, re.search(self.ERROR_INFO_PATTERN, self.html).group(1))
        except Exception:
            self.logError("Unknown error occurred", errmsg)

        if errmsg is "invalid":
            self.fail(_("File not available"))

        elif errmsg in ("freelimit", "size", "proxy"):
            self.fail(_("Premium account needed"))

        elif errmsg in ("expired", "server"):
            self.retry(wait_time=600, reason=errmsg)

        elif 'slot' in errmsg:
            self.wantReconnect = True
            self.retry(24, 3600, errmsg)

        else:
            self.wantReconnect = True
            self.retry(wait_time=60, reason=errmsg)


getInfo = create_getInfo(ShareonlineBiz)
