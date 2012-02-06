# -*- coding: utf-8 -*-
"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.

    @author: zoidberg
"""

import re
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo

def convertDecimalPrefix(m):
    # decimal prefixes used in filesize and traffic
    return ("%%.%df" % {'k':3,'M':6,'G':9}[m.group(2)] % float(m.group(1))).replace('.','')     

class UlozTo(SimpleHoster):
    __name__ = "UlozTo"
    __type__ = "hoster"
    __pattern__ = r"http://(\w*\.)?(uloz\.to|ulozto\.(cz|sk|net)|bagruj.cz|zachowajto.pl)/(?:live/)?(?P<id>\d+/[^/?]*)"
    __version__ = "0.83"
    __description__ = """uloz.to"""
    __author_name__ = ("zoidberg")

    FILE_NAME_PATTERN = r'<a href="#download" class="jsShowDownload">(?P<N>[^<]+)</a>' 
    FILE_SIZE_PATTERN = r'<span id="fileSize">(?P<S>[^<]+)</span>'   
    FILE_SIZE_REPLACEMENTS = [('([0-9.]+)\s([kMG])B', convertDecimalPrefix)]       
    FILE_OFFLINE_PATTERN = ur'<title>(404 - Page not found|Stránka nenalezena|Nie można wyświetlić strony)</title>'
    
    PASSWD_PATTERN = r'<input type="password" class="text" name="file_password" id="frmfilepasswordForm-file_password" />'
    VIPLINK_PATTERN = r'<a href="[^"]*\?disclaimer=1" class="linkVip">'    
    FREE_URL_PATTERN = r'<div class="freeDownloadForm"><form action="([^"]+)"'
    PREMIUM_URL_PATTERN = r'<div class="downloadForm"><form action="([^"]+)"'
    CAPTCHA_PATTERN = r'<img class="captcha" src="(.*?(\d+).png)" alt="" />'
    
    def process(self, pyfile):        
        self.url = "http://www.ulozto.net/" + re.match(self.__pattern__, pyfile.url).group('id')   
        
        self.html = self.load(self.url, decode=True)
        
        # password protected links
        passwords = self.getPassword().splitlines()       
        while self.PASSWD_PATTERN in self.html:
            if passwords:
                password = passwords.pop(0)
                self.logInfo("Password protected link, trying " + password)
                self.html = self.load(self.url, get = {"do": "filepasswordForm-submit"}, post={"file_password": password, "fpwdsend": 'Odeslat'}, cookies=True)
            else:
                self.fail("No or incorrect password")
        
        self.file_info = self.getFileInfo()
                
        # adult content    
        if re.search(self.VIPLINK_PATTERN, self.html):
            self.html = self.load(self.url, get={"disclaimer": "1"})
        
        if self.premium and self.checkTrafficLeft():
            self.handlePremium()
        else: 
            self.handleFree()
            
    def handleFree(self):    
        parsed_url = self.findDownloadURL(premium=False)

        # get and decrypt captcha
        captcha_id = self.getStorage("captcha_id")
        captcha_text = self.getStorage("captcha_text")
        captcha_url = "DUMMY"

        if not captcha_id or not captcha_text:
            found = re.search(self.CAPTCHA_PATTERN, self.html)
            if not found: self.parseError("CAPTCHA")
            captcha_url, captcha_id = found.groups()

            captcha_text = self.decryptCaptcha(captcha_url)
        
        self.log.debug('CAPTCHA_URL:' + captcha_url + ' CAPTCHA ID:' + captcha_id + ' CAPTCHA TEXT:' + captcha_text)

        # download and check        
        self.download(parsed_url, post={"captcha[id]": captcha_id, "captcha[text]": captcha_text, "freeDownload": "Download"}, cookies=True)
        self.doCheckDownload()   
        
        self.setStorage("captcha_id", captcha_id)
        self.setStorage("captcha_text", captcha_text)
    
    def handlePremium(self):
        parsed_url = self.findDownloadURL(premium=True)
        self.download(parsed_url, post={"download": "Download"})
        self.doCheckDownload()
        
    def findDownloadURL(self, premium=False):
        msg = "%s link" % ("Premium" if premium else "Free")
        found = re.search(self.PREMIUM_URL_PATTERN if premium else self.FREE_URL_PATTERN, self.html)
        if not found: self.parseError(msg)
        parsed_url = "http://www.ulozto.net" + found.group(1)
        self.logDebug("%s: %s" % (msg, parsed_url))
        return parsed_url
    
    def doCheckDownload(self):
        check = self.checkDownload({
            "wrong_captcha": re.compile(self.CAPTCHA_PATTERN),
            "offline": re.compile(self.FILE_OFFLINE_PATTERN),
            "passwd": self.PASSWD_PATTERN,
            "paralell_dl": u'<h2 class="center">Z Vašeho počítače se již stahuje</h2>'
        })

        if check == "wrong_captcha":
            self.delStorage("captcha_id")
            self.delStorage("captcha_text")
            self.invalidCaptcha()
            self.retry(reason="Wrong captcha code")
        elif check == "offline":
            self.offline()
        elif check == "passwd":
            self.fail("Wrong password")
        elif check == "paralell_dl":
            self.setWait(600, True)
            self.wait()
            self.retry()    

getInfo = create_getInfo(UlozTo)        