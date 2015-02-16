# -*- coding: utf-8 -*-

import re

from pyload.plugin.internal.captcha import SolveMedia
from pyload.plugin.internal.SimpleHoster import SimpleHoster, parseFileInfo
from pyload.network.RequestFactory import getURL


def replace_eval(js_expr):
    return js_expr.replace(r'eval("', '').replace(r"\'", r"'").replace(r'\"', r'"')


def checkHTMLHeader(url):
    try:
        for _i in xrange(3):
            header = getURL(url, just_header=True)

            for line in header.splitlines():
                line = line.lower()

                if 'location' in line:
                    url = line.split(':', 1)[1].strip()
                    if 'error.php?errno=320' in url:
                        return url, 1

                    if not url.startswith('http://'):
                        url = 'http://www.mediafire.com' + url

                    break

                elif 'content-disposition' in line:
                    return url, 2
            else:
                break
    except Exception:
        return url, 3
    else:
        return url, 0


def getInfo(urls):
    for url in urls:
        location, status = checkHTMLHeader(url)

        if status:
            file_info = (url, 0, status, url)
        else:
            file_info = parseFileInfo(MediafireCom, url, getURL(url, decode=True))

        yield file_info


class MediafireCom(SimpleHoster):
    __name    = "MediafireCom"
    __type    = "hoster"
    __version = "0.84"

    __pattern = r'http://(?:www\.)?mediafire\.com/(file/|(view/?|download\.php)?\?)(\w{11}|\w{15})($|/)'

    __description = """Mediafire.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("stickell", "l.stickell@yahoo.it")]


    NAME_PATTERN    = r'<META NAME="description" CONTENT="(?P<N>[^"]+)"/>'
    INFO_PATTERN    = r'oFileSharePopup\.ald\(\'(?P<ID>[^\']*)\',\'(?P<N>[^\']*)\',\'(?P<S>[^\']*)\',\'\',\'(?P<H>[^\']*)\'\)'
    OFFLINE_PATTERN = r'class="error_msg_title"> Invalid or Deleted File. </div>'

    PASSWORD_PATTERN = r'<form name="form_password"'


    def setup(self):
        self.multiDL = False


    def process(self, pyfile):
        pyfile.url = re.sub(r'/view/?\?', '/?', pyfile.url)

        self.link, result = checkHTMLHeader(pyfile.url)
        self.logDebug("Location (%d): %s" % (result, self.link))

        if result == 0:
            self.html = self.load(self.link, decode=True)
            self.checkCaptcha()
            self.multiDL = True
            self.check_data = self.getFileInfo()

            if self.account:
                self.handlePremium(pyfile)
            else:
                self.handleFree(pyfile)
        elif result == 1:
            self.offline()
        else:
            self.multiDL = True
            self.download(self.link, disposition=True)


    def handleFree(self, pyfile):
        if self.PASSWORD_PATTERN in self.html:
            password = self.getPassword()

            if password:
                self.logInfo(_("Password protected link, trying ") + password)
                self.html = self.load(self.link, post={"downloadp": password})

                if self.PASSWORD_PATTERN in self.html:
                    self.fail(_("Incorrect password"))
            else:
                self.fail(_("No password found"))

        m = re.search(r'kNO = r"(http://.*?)";', self.html)
        if m is None:
            self.error(_("No download URL"))

        download_url = m.group(1)
        self.download(download_url)


    def checkCaptcha(self):
        solvemedia = SolveMedia(self)
        response, challenge = solvemedia.challenge()
        self.html = self.load(self.link,
                              post={'adcopy_challenge': challenge,
                                    'adcopy_response' : response},
                              decode=True)
