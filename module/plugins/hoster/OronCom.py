# -*- coding: utf-8 -*-
import re

from module.plugins.Hoster import Hoster
from module.network.RequestFactory import getURL
from module.plugins.ReCaptcha import ReCaptcha

def getInfo(urls):
    result = []

    for url in urls:
        html = getURL(url).replace("\n","")
        html = html.replace("\t", "")
        if "File could not be found" in html:
            result.append((url, 0, 1, url))
            continue

        m = re.search(OronCom.FILE_INFO_PATTERN, html)
        if m:
            name = m.group(1)
            hSize = float(m.group(2).replace(",", "."))
            pow = {'Kb':1, 'Mb': 2, 'Gb':3}[m.group(3)]
            size = int(hSize * 1024 ** pow)
        else:
            name = url
            size = 0

        result.append((name, size, 2, url))
    yield result

class OronCom(Hoster):
    __name__ = "OronCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:www.)?oron.com/"
    __version__ = "0.1"
    __description__ = "File Hoster: Oron.com"
    __author_name__ = "chrox"

    FILE_INFO_PATTERN = r'<td align="right">.*?Filename: .*?>(.*?)</b><br>File size: ([0-9,.]+) (Kb|Mb|Gb)'

    def init(self):
        self.multiDL = False
        self.file_id = re.search(r'http://(?:www.)?oron.com/([a-zA-Z0-9]+)', self.pyfile.url).group(1)
        self.logDebug("File id is %s" % self.file_id)
        self.pyfile.url = "http://oron.com/" + self.file_id

    def process(self, pyfile):
        self.html = self.load(self.pyfile.url, ref=False, decode=True).replace("\n","")
        if "File could not be found" in self.html:
            self.offline()
        self.html = self.html.replace("\t", "")
        m = re.search(self.FILE_INFO_PATTERN, self.html)
        if m:
            pyfile.name = m.group(1)
            hSize = float(m.group(2).replace(",", "."))
            pow = {'Kb':1, 'Mb': 2, 'Gb':3}[m.group(3)]
            pyfile.size = int(hSize * 1024 ** pow)
            self.logDebug("File Size: %d" % pyfile.size)
        else:
            self.logDebug("Name and/or size not found.")

        self.handleFree(pyfile)

    def handleFree(self, pyfile):
        self.html = self.load(self.pyfile.url, ref=False, decode=True).replace("\n","")
        if "download1" in self.html:
            post_url = "http://oron.com/"+self.file_id
            post_dict = {'op': 'download1', 'usr_login': '', 'id':self.file_id, 'fname':pyfile.name, 'referer':'', 'method_free':' Regular Download '}
            self.html = self.load(post_url, post=post_dict, ref=False, decode=True).encode("utf-8")
            if '<p class="err">' in self.html:
                time_list = re.findall(r'\d+(?=\s[a-z]+,)|\d+(?=\s.*?until)',self.html)
                tInSec = 0
                for t in time_list:
                    tInSec = tInSec + int(t)*60**(len(time_list)-time_list.index(t)-1)
                self.setWait(tInSec,True)
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
                downloadLink = ""
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
                        downloadLink = re.search('href="(.*?)" class="atitle"',self.html)
                        break
                    
                if not downloadLink:
                    self.fail("Could not find download link")

                self.logDebug("Download url found: %s" % downloadLink.group(1))
                self.download(downloadLink.group(1))
        else:
            self.logError("error in parsing site")
