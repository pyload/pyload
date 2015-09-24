# -*- coding: utf-8 -*-

import re
import time
import urllib

from module.network.RequestFactory import getURL as get_url
from module.plugins.captcha.ReCaptcha import ReCaptcha
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class ShareonlineBiz(SimpleHoster):
    __name__    = "ShareonlineBiz"
    __type__    = "hoster"
    __version__ = "0.56"
    __status__  = "testing"

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
    def api_info(cls, url):
        info = super(ShareonlineBiz, cls).api_info(url)

        field = get_url("http://api.share-online.biz/linkcheck.php",
                        get={'md5'  : "1",
                             'links': re.match(cls.__pattern__, url).group("ID")}).split(";")

        try:
            if field[1] == "OK":
                info['fileid']   = field[0]
                info['status']   = 2
                info['name']     = field[2]
                info['size']     = field[3]  #: In bytes
                info['md5']      = field[4].strip().lower().replace("\n\n", "")  #: md5

            elif field[1] in ("DELETED", "NOTFOUND"):
                info['status'] = 1

        except IndexError:
            pass

        return info


    def setup(self):
        self.resume_download = self.premium
        self.multiDL        = False


    def handle_captcha(self):
        recaptcha = ReCaptcha(self)

        for _i in xrange(5):
            response, challenge = recaptcha.challenge(self.RECAPTCHA_KEY)

            m = re.search(r'var wait=(\d+);', self.html)
            self.set_wait(int(m.group(1)) if m else 30)

            res = self.load("%s/free/captcha/%d" % (self.pyfile.url, int(time.time() * 1000)),
                            post={'dl_free'                  : "1",
                                  'recaptcha_challenge_field': challenge,
                                  'recaptcha_response_field' : response})
            if res != "0":
                self.captcha.correct()
                return res
            else:
                self.captcha.invalid()
        else:
            self.captcha.invalid()
            self.fail(_("No valid captcha solution received"))


    def handle_free(self, pyfile):
        self.wait(3)

        self.html = self.load("%s/free/" % pyfile.url,
                              post={'dl_free': "1", 'choice': "free"})

        self.check_errors()

        res = self.handle_captcha()
        self.link = res.decode('base64')

        if not self.link.startswith("http://"):
            self.error(_("Wrong download url"))

        self.wait()


    def check_file(self):
        check = self.check_download({'cookie': re.compile(r'<div id="dl_failure"'),
                                    'fail'  : re.compile(r"<title>Share-Online")})

        if check == "cookie":
            self.captcha.invalid()
            self.retry(5, 60, _("Cookie failure"))

        elif check == "fail":
            self.captcha.invalid()
            self.retry(5, 5 * 60, _("Download failed"))

        return super(ShareonlineBiz, self).check_file()


    def handle_premium(self, pyfile):  #: Should be working better loading (account) api internally
        html = self.load("https://api.share-online.biz/account.php",
                         get={'username': self.account.user,
                              'password': self.account.get_info(self.account.user)['login']['password'],
                              'act'     : "download",
                              'lid'     : self.info['fileid']})

        self.api_data = dlinfo = {}

        for line in html.splitlines():
            key, value = line.split(": ")
            dlinfo[key.lower()] = value

        self.log_debug(dlinfo)

        if dlinfo['status'] != "online":
            self.offline()
        else:
            pyfile.name = dlinfo['name']
            pyfile.size = int(dlinfo['size'])

            self.link = dlinfo['url']

            if self.link == "server_under_maintenance":
                self.temp_offline()
            else:
                self.multiDL = True


    def check_errors(self):
        m = re.search(r"/failure/(.*?)/1", self.req.lastEffectiveURL)
        if m is None:
            self.info.pop('error', None)
            return

        errmsg = m.group(1).lower()

        try:
            self.log_error(errmsg, re.search(self.ERROR_PATTERN, self.html).group(1))

        except Exception:
            self.log_error(_("Unknown error occurred"), errmsg)

        if errmsg == "invalid":
            self.fail(_("File not available"))

        elif errmsg in ("freelimit", "size", "proxy"):
            self.fail(_("Premium account needed"))

        elif errmsg in ("expired", "server"):
            self.retry(wait_time=600, msg=errmsg)

        elif errmsg == "full":
            self.retry(10, 600, _("Server is full"))

        elif 'slot' in errmsg:
            self.wantReconnect = True
            self.retry(24, 3600, errmsg)

        else:
            self.wantReconnect = True
            self.retry(wait_time=60, msg=errmsg)


getInfo = create_getInfo(ShareonlineBiz)
