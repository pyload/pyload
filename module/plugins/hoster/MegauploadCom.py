#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

from module.plugins.Hoster import Hoster

from module.network.RequestFactory import getURL

from module.utils import html_unescape
from datatypes.PyFile import statusMap

def getInfo(urls):
    yield [(url, 0, 1, url) for url in urls]

    
def _translateAPIFileInfo(apiFileId, apiFileDataMap, apiHosterMap):
    
    # Translate
    fileInfo = {}
    try:
        fileInfo['status'] = MegauploadCom.API_STATUS_MAPPING[apiFileDataMap[apiFileId]]
        fileInfo['name'] = html_unescape(apiFileDataMap['n'])
        fileInfo['size'] = int(apiFileDataMap['s'])
        fileInfo['hoster'] = apiHosterMap[apiFileDataMap['d']]        
    except:
        pass

    return fileInfo

class MegauploadCom(Hoster):
    __name__ = "MegauploadCom"
    __type__ = "hoster"
    __pattern__ = r"http://[\w\.]*?(megaupload)\.com/.*?(\?|&)d=(?P<id>[0-9A-Za-z]+)"
    __version__ = "0.32"
    __description__ = """Megaupload.com Download Hoster"""
    __author_name__ = ("spoob")
    __author_mail__ = ("spoob@pyload.org")
    
    API_URL = "http://megaupload.com/mgr_linkcheck.php"
    API_STATUS_MAPPING = {"0": statusMap['online'], "1": statusMap['offline'], "3": statusMap['temp. offline']}
    
    FILE_URL_PATTERN = r'<a href="([^"]+)" class="download_regular_usual"' 
    PREMIUM_URL_PATTERN = r'href=\"(http://[^\"]*?)\" class=\"download_premium_but\">'
    
    def init(self):
        self.html = [None, None]
        if self.account:
            self.premium = self.account.getAccountInfo(self.user)["premium"]

        if not self.premium:
            self.multiDL = False
            self.chunkLimit = 1

        self.api = {}
        
        self.fileID = re.search(self.__pattern__, self.pyfile.url).group("id")
        self.pyfile.url = "http://www.megaupload.com/?d=" + self.fileID

        
    def process(self, pyfile):
        self.fail("Hoster not longer available")

    def download_html(self):        
        for i in range(3):
            self.html[0] = self.load(self.pyfile.url)
            self.html[1] = self.html[0] # in case of no captcha, this already contains waiting time, etc
            count = 0
            if "The file that you're trying to download is larger than 1 GB" in self.html[0]:
                self.fail(_("You need premium to download files larger than 1 GB"))
                
            if re.search(r'<input[^>]*name="filepassword"', self.html[0]):
                pw = self.getPassword()
                if not pw:
                    self.fail(_("The file is password protected, enter a password and restart."))

                self.html[1] = self.load(self.pyfile.url, post={"filepassword":pw})
                break # looks like there is no captcha for pw protected files

            while "document.location='http://www.megaupload.com/?c=msg" in self.html[0]:
                # megaupload.com/?c=msg usually says: Please check back in 2 minutes,
                # so we can spare that http request
                self.setWait(120)
                if count > 1:
                    self.wantReconnect = True

                self.wait()
                
                self.html[0] = self.load(self.pyfile.url)
                count += 1
                if count > 5:
                    self.fail(_("Megaupload is currently blocking your IP. Try again later, manually."))
            
            try:
                url_captcha_html = re.search('(http://[\w\.]*?megaupload\.com/gencap.php\?.*\.gif)', self.html[0]).group(1)
            except:
                continue

            captcha = self.decryptCaptcha(url_captcha_html)
            captchacode = re.search('name="captchacode" value="(.*)"', self.html[0]).group(1)
            megavar = re.search('name="megavar" value="(.*)">', self.html[0]).group(1)
            self.html[1] = self.load(self.pyfile.url, post={"captcha": captcha, "captchacode": captchacode, "megavar": megavar})
            if re.search(r"Waiting time before each download begins", self.html[1]) is not None:
                break

    def download_api(self):

        # MU API request 
        fileId = self.pyfile.url.split("=")[-1] # Get file id from url
        apiFileId = "id0"
        post = {apiFileId: fileId}
        response = getURL(self.API_URL, post=post, decode = True)    
        self.log.debug("%s: API response [%s]" % (self.__name__, response))
        
        # Translate API response
        parts = [re.split(r"&(?!amp;|#\d+;)", x) for x in re.split(r"&?(?=id[\d]+=)", response)]
        apiHosterMap = dict([elem.split('=') for elem in parts[0]])
        apiFileDataMap = dict([elem.split('=') for elem in parts[1]])        
        self.api = _translateAPIFileInfo(apiFileId, apiFileDataMap, apiHosterMap)

        # File info
        try:
            self.pyfile.status = self.api['status']
            self.pyfile.name = self.api['name'] 
            self.pyfile.size = self.api['size']
        except KeyError:
            self.log.warn("%s: Cannot recover all file [%s] info from API response." % (self.__name__, fileId))
        
        # Fail if offline
        if self.pyfile.status == statusMap['offline']:
            self.offline()

    def get_file_url(self):
        search = re.search(self.FILE_URL_PATTERN, self.html[1])
        return search.group(1).replace(" ", "%20") if search else None

    def get_file_name(self):
        try:
            name =  self.api["name"]
        except KeyError:
            file_name_pattern = 'id="downloadlink"><a href="(.*)" onclick="'
            name = re.search(file_name_pattern, self.html[1]).group(1).split("/")[-1]

        return html_unescape(name)

    def get_wait_time(self):
        time = re.search(r"count=(\d+);", self.html[1])
        if time:
            return time.group(1)
        else:
            return 60

    def file_exists(self):
        #self.download_html()
        if re.search(r"Unfortunately, the link you have clicked is not available.", self.html[0]) is not None or \
            re.search(r"Download limit exceeded", self.html[0]) is not None:
            return False
            
        if re.search("The file you are trying to access is temporarily unavailable", self.html[0]) is not None:
            self.setWait(120)
            self.log.debug("%s: The file is temporarily not available. Waiting 2 minutes." % self.__name__)
            self.wait()
            
            self.download_html()
            if re.search("The file you are trying to access is temporarily unavailable", self.html[0]) is not None:
                self.fail(_("Looks like the file is still not available. Retry downloading later, manually."))
            
        if re.search("The password you have entered is not correct", self.html[1]):
            self.fail(_("Wrong password for download link."))
            
        return True
