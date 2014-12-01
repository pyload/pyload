# -*- coding: utf-8 -*-

import re

from time import time

from pyload.network.RequestFactory import getURL
from pyload.plugins.internal.Hoster import Hoster
from pyload.plugins.Plugin import chunks
from pyload.plugins.internal.CaptchaService import ReCaptcha


def getInfo(urls):
    api_url_base = "http://api.share-online.biz/linkcheck.php"

    urls = [url.replace("https://", "http://") for url in urls]

    for chunk in chunks(urls, 90):
        api_param_file = {"links": "\n".join(x.replace("http://www.share-online.biz/dl/", "").rstrip("/") for x in
                                             chunk)}  # api only supports old style links
        html = getURL(api_url_base, post=api_param_file, decode=True)
        result = []
        for i, res in enumerate(html.split("\n")):
            if not res:
                continue
            fields = res.split(";")

            if fields[1] == "OK":
                status = 2
            elif fields[1] in ("DELETED", "NOT FOUND"):
                status = 1
            else:
                status = 3

            result.append((fields[2], int(fields[3]), status, chunk[i]))
        yield result


class ShareonlineBiz(Hoster):
    __name__    = "ShareonlineBiz"
    __type__    = "hoster"
    __version__ = "0.41"

    __pattern__ = r'https?://(?:www\.)?(share-online\.biz|egoshare\.com)/(download\.php\?id=|dl/)(?P<ID>\w+)'

    __description__ = """Shareonline.biz hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("spoob", "spoob@pyload.org"),
                       ("mkaay", "mkaay@mkaay.de"),
                       ("zoidberg", "zoidberg@mujmail.cz"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    ERROR_INFO_PATTERN = r'<p class="b">Information:</p>\s*<div>\s*<strong>(.*?)</strong>'


    def setup(self):
        self.file_id = re.match(self.__pattern__, self.pyfile.url).group("ID")
        self.pyfile.url = "http://www.share-online.biz/dl/" + self.file_id

        self.resumeDownload = self.premium
        self.multiDL = False

        self.check_data = None


    def process(self, pyfile):
        if self.premium:
            self.handlePremium()
        else:
            self.handleFree()

        if self.api_data:
            self.check_data = {"size": int(self.api_data['size']), "md5": self.api_data['md5']}


    def loadAPIData(self):
        api_url_base = "http://api.share-online.biz/linkcheck.php?md5=1"
        api_param_file = {"links": self.file_id}  #: api only supports old style links
        html = self.load(api_url_base, cookies=False, post=api_param_file, decode=True)

        fields = html.split(";")
        self.api_data = {"fileid": fields[0],
                         "status": fields[1]}
        if not self.api_data['status'] == "OK":
            self.offline()
        else:
            self.api_data['filename'] = fields[2]
            self.api_data['size'] = fields[3]  #: in bytes
            self.api_data['md5'] = fields[4].strip().lower().replace("\n\n", "")  #: md5


    def handleFree(self):
        self.loadAPIData()
        self.pyfile.name = self.api_data['filename']
        self.pyfile.size = int(self.api_data['size'])

        self.html = self.load(self.pyfile.url, cookies=True)  #: refer, stuff
        self.setWait(3)
        self.wait()

        self.html = self.load("%s/free/" % self.pyfile.url, post={"dl_free": "1", "choice": "free"}, decode=True)
        self.checkErrors()

        m = re.search(r'var wait=(\d+);', self.html)

        recaptcha = ReCaptcha(self)
        for _i in xrange(5):
            challenge, response = recaptcha.challenge("6LdatrsSAAAAAHZrB70txiV5p-8Iv8BtVxlTtjKX")
            self.setWait(int(m.group(1)) if m else 30)
            res = self.load("%s/free/captcha/%d" % (self.pyfile.url, int(time() * 1000)),
                            post={'dl_free': '1',
                                  'recaptcha_challenge_field': challenge,
                                  'recaptcha_response_field': response})

            if not res == '0':
                self.correctCaptcha()
                break
            else:
                self.invalidCaptcha()
        else:
            self.invalidCaptcha()
            self.fail(_("No valid captcha solution received"))

        download_url = res.decode("base64")
        if not download_url.startswith("http://"):
            self.error(_("Wrong download url"))

        self.wait()
        self.download(download_url)
        # check download
        check = self.checkDownload({
            "cookie": re.compile(r'<div id="dl_failure"'),
            "fail": re.compile(r"<title>Share-Online")
        })
        if check == "cookie":
            self.invalidCaptcha()
            self.retry(5, 60, "Cookie failure")
        elif check == "fail":
            self.invalidCaptcha()
            self.retry(5, 5 * 60, "Download failed")
        else:
            self.correctCaptcha()


    def handlePremium(self):  #: should be working better loading (account) api internally
        self.account.getAccountInfo(self.user, True)
        html = self.load("http://api.share-online.biz/account.php",
                        {"username": self.user, "password": self.account.accounts[self.user]['password'],
                         "act": "download", "lid": self.file_id})

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
            return

        err = m.group(1)
        try:
            self.logError(err, re.search(self.ERROR_INFO_PATTERN, self.html).group(1))
        except Exception:
            self.logError(err, "Unknown error occurred")

        if err == "invalid":
            self.fail(_("File not available"))
        elif err in ("freelimit", "size", "proxy"):
            self.fail(_("Premium account needed"))
        else:
            if err in 'server':
                self.setWait(600, False)
            elif err in 'expired':
                self.setWait(30, False)
            else:
                self.setWait(300, True)

            self.wait()
            self.retry(max_tries=25, reason=err)
