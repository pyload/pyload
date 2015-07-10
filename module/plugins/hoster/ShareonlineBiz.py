# -*- coding: utf-8 -*-

import re
import time
import urllib
import urlparse

from module.network.RequestFactory import getURL
from module.plugins.internal.ReCaptcha import ReCaptcha
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class ShareonlineBiz(SimpleHoster):
    __name__    = "ShareonlineBiz"
    __type__    = "hoster"
    __version__ = "0.54"

    __pattern__ = r'https?://(?:www\.)?(share-online\.biz|egoshare\.com)/(download\.php\?id=|dl/)(?P<ID>\w+)'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """Shareonline.biz hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("spoob", "spoob@pyload.org"),
                       ("mkaay", "mkaay@mkaay.de"),
                       ("zoidberg", "zoidberg@mujmail.cz"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    URL_REPLACEMENTS = [(__pattern__ + ".*", "http://www.share-online.biz/dl/\g<ID>")]

    CHECK_TRAFFIC = True

    RECAPTCHA_KEY = "6LdatrsSAAAAAHZrB70txiV5p-8Iv8BtVxlTtjKX"

    ERROR_PATTERN = r'<p class="b">Information:</p>\s*<div>\s*<strong>(.*?)</strong>'


    @classmethod
    def apiInfo(cls, url):
        info = super(ShareonlineBiz, cls).apiInfo(url)

        field = getURL("http://api.share-online.biz/linkcheck.php",
                       get={'md5'  : "1",
                            'links': re.match(cls.__pattern__, url).group("ID")},
                       decode=True).split(";")

        info['status'] = 1
        try:
            if field[1] == "OK":
                info['fileid']   = field[0]
                info['status']   = 2
                info['name']     = field[2]
                info['size']     = field[3]  #: in bytes
                info['md5']      = field[4].strip().lower().replace("\n\n", "")  #: md5
        except IndexError:
            pass

        return info


    def setup(self):
        self.resumeDownload = self.premium
        self.multiDL        = False


    def handleCaptcha(self):
        recaptcha = ReCaptcha(self)

        for _i in xrange(5):
            response, challenge = recaptcha.challenge(self.RECAPTCHA_KEY)

            m = re.search(r'var wait=(\d+);', self.html)
            self.setWait(int(m.group(1)) if m else 30)

            res = self.load("%s/free/captcha/%d" % (self.pyfile.url, int(time.time() * 1000)),
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


    def handleFree(self, pyfile):
        self.wait(3)

        self.html = self.load("%s/free/" % pyfile.url,
                              post={'dl_free': "1", 'choice': "free"},
                              decode=True)

        self.checkErrors()

        res = self.handleCaptcha()
        self.link = res.decode('base64')

        if not self.link.startswith("http://"):
            self.error(_("Wrong download url"))

        self.wait()


    def checkFile(self):
        check = self.checkDownload({'cookie': re.compile(r'<div id="dl_failure"'),
                                    'fail'  : re.compile(r"<title>Share-Online")})

        if check == "cookie":
            self.invalidCaptcha()
            self.retry(5, 60, _("Cookie failure"))

        elif check == "fail":
            self.invalidCaptcha()
            self.retry(5, 5 * 60, _("Download failed"))

        return super(ShareonlineBiz, self).checkFile()


    def handlePremium(self, pyfile):  #: should be working better loading (account) api internally
        html = self.load("http://api.share-online.biz/account.php",
                         get={'username': self.user,
                              'password': self.account.getAccountData(self.user)['password'],
                              'act'     : "download",
                              'lid'     : self.info['fileid']})

        self.api_data = dlinfo = {}

        for line in html.splitlines():
            key, value = line.split(": ")
            dlinfo[key.lower()] = value

        self.logDebug(dlinfo)

        if not dlinfo['status'] == "online":
            self.offline()
        else:
            pyfile.name = dlinfo['name']
            pyfile.size = int(dlinfo['size'])

            self.link = dlinfo['url']

            if self.link == "server_under_maintenance":
                self.tempOffline()
            else:
                self.multiDL = True


    def checkErrors(self):
        m = re.search(r"/failure/(.*?)/1", self.req.lastEffectiveURL)
        if m is None:
            self.info.pop('error', None)
            return

        errmsg = m.group(1).lower()

        try:
            self.logError(errmsg, re.search(self.ERROR_PATTERN, self.html).group(1))
        except Exception:
            self.logError("Unknown error occurred", errmsg)

        if errmsg is "invalid":
            self.fail(_("File not available"))

        elif errmsg in ("full", "freelimit", "size", "proxy"):
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
