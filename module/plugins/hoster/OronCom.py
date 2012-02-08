# -*- coding: utf-8 -*-
import re

from module.plugins.Hoster import Hoster
from module.network.RequestFactory import getURL
from module.plugins.ReCaptcha import ReCaptcha
from module.utils import parseFileSize

def getInfo(urls):
    result = []

    for url in urls:
        html = getURL(url).replace("\n", "")
        html = html.replace("\t", "")
        if "File could not be found" in html:
            result.append((url, 0, 1, url))
            continue

        m = re.search(OronCom.FILE_INFO_PATTERN, html, re.MULTILINE)
        if m:
            name = m.group(1)
            size = parseFileSize(m.group(2), m.group(3))
        else:
            name = url
            size = 0

        result.append((name, size, 2, url))
    yield result


class OronCom(Hoster):
    __name__ = "OronCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:www.)?oron.com/(?!folder)\w+"
    __version__ = "0.16"
    __description__ = "Oron.com Hoster Plugin"
    __author_name__ = ("chrox", "DHMH")
    __author_mail__ = ("chrox@pyload.org", "webmaster@pcProfil.de")

    FILE_INFO_PATTERN = r'(?:Filename|Dateiname): <b class="f_arial f_14px">(.*?)</b>\s*<br>\s*(?:Größe|File size): ([0-9,\.]+) (Kb|Mb|Gb)'

    def init(self):
        self.resumeDownload = self.multiDL = True if self.account else False
        self.chunkLimit = 1
        self.file_id = re.search(r'http://(?:www.)?oron.com/([a-zA-Z0-9]+)', self.pyfile.url).group(1)
        self.logDebug("File id is %s" % self.file_id)
        self.pyfile.url = "http://oron.com/" + self.file_id

    def process(self, pyfile):
        #self.load("http://oron.com/?op=change_lang&lang=german")
        # already logged in, so the above line shouldn't be necessary
        self.html = self.load(self.pyfile.url, ref=False, decode=True).encode("utf-8").replace("\n", "")
        if "File could not be found" in self.html or "Datei nicht gefunden" in self.html or \
                                        "This file has been blocked for TOS violation." in self.html:
            self.offline()
        self.html = self.html.replace("\t", "")
        m = re.search(self.FILE_INFO_PATTERN, self.html)
        if m:
            pyfile.name = m.group(1)
            pyfile.size = parseFileSize(m.group(2), m.group(3))
            self.logDebug("File Size: %s" % pyfile.formatSize())
        else:
            self.logDebug("Name and/or size not found.")

        if self.account:
            self.handlePremium()
        else:
            self.handleFree()

    def handleFree(self):
        #self.load("http://oron.com/?op=change_lang&lang=german")
        # already logged in, so the above line shouldn't be necessary
        self.html = self.load(self.pyfile.url, ref=False, decode=True).replace("\n", "")
        if "download1" in self.html:
            post_url = "http://oron.com/" + self.file_id
            post_dict = {'op': 'download1',
                         'usr_login': '',
                         'id': self.file_id,
                         'fname': self.pyfile.name,
                         'referer': '',
                         'method_free': ' Regular Download '}

            self.html = self.load(post_url, post=post_dict, ref=False, decode=True).encode("utf-8")
            if '<p class="err">' in self.html:
                time_list = re.findall(r'\d+(?=\s[a-z]+,)|\d+(?=\s.*?until)', self.html)
                tInSec = 0
                for t in time_list:
                    tInSec += int(t) * 60 ** (len(time_list) - time_list.index(t) - 1)
                self.setWait(tInSec, True)
                self.wait()
                self.retry()

            if "download2" in self.html:
                post_dict['op'] = 'download2'
                post_dict['method_free'] = 'Regular Download'
                post_dict['method_premium'] = ''
                post_dict['down_direct'] = '1'
                post_dict['btn_download'] = ' Create Download Link '
                del(post_dict['fname'])

                re_captcha = ReCaptcha(self)
                downloadLink = None
                for i in range(5):
                    m = re.search('name="rand" value="(.*?)">', self.html)
                    post_dict['rand'] = m.group(1)
                    challengeId = re.search(r'/recaptcha/api/challenge[?k=]+([^"]+)', self.html)
                    challenge, result = re_captcha.challenge(challengeId.group(1))
                    post_dict['recaptcha_challenge_field'] = challenge
                    post_dict['recaptcha_response_field'] = result
                    self.html = self.load(post_url, post=post_dict)
                    m = re.search('<p class="err">(.*?)</p>', self.html)
                    if m:
                        if m.group(1) == "Wrong captcha":
                            self.invalidCaptcha()
                            self.logDebug("Captcha failed")
                    if 'class="atitle">Download File' in self.html:
                        self.correctCaptcha()
                        downloadLink = re.search('href="(.*?)" class="atitle"', self.html)
                        break

                if not downloadLink:
                    self.fail("Could not find download link")

                self.logDebug("Download url found: %s" % downloadLink.group(1))
                self.download(downloadLink.group(1))
        else:
            self.logError("error in parsing site")

    def handlePremium(self):
        info = self.account.getAccountInfo(self.user, True)
        self.logDebug("Traffic left: %s" % info['trafficleft'])
        self.logDebug("File Size: %d" % int(self.pyfile.size / 1024))

        if int(self.pyfile.size / 1024) > info["trafficleft"]:
            self.logInfo(_("Not enough traffic left"))
            self.account.empty(self.user)
            self.fail(_("Traffic exceeded"))

        post_url = "http://oron.com/" + self.file_id
        m = re.search('name="rand" value="(.*?)">', self.html)
        rand = m.group(1)
        post_dict = {'down_direct': '1', 'id': self.file_id, 'op': 'download2', 'rand': rand, 'referer': '',
                     'method_free': '', 'method_premium': '1'}

        self.html = self.load(post_url, post=post_dict, ref=False, decode=True).encode("utf-8")
        link = re.search('href="(.*?)" class="atitle"', self.html).group(1)
        self.download(link)
