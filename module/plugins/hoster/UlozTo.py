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
    __pattern__ = r"http://(\w*\.)?(uloz\.to|ulozto\.(cz|sk|net)|bagruj.cz|zachowajto.pl)/.*"
    __version__ = "0.81"
    __description__ = """uloz.to"""
    __author_name__ = ("zoidberg")

    FILE_NAME_PATTERN = r'<a share_url="[^&]*&amp;t=(?P<N>[^"]+)"'
    #FILE_NAME_PATTERN = r'<h2 class="nadpis" style="margin-left:196px;"><a href="[^"]+">(?P<N>[^<]+)</a></h2>'
    FILE_SIZE_PATTERN = r'<div class="info_velikost" style="top:-55px;">\s*<div>[^<]*\s+(?P<S>[0-9.]+\s[kMG]B)\s*</div>\s*</div>'   
    FILE_SIZE_REPLACEMENTS = [('([0-9.]+)\s([kMG])B', convertDecimalPrefix)]       
    FILE_OFFLINE_PATTERN = r'http://www.uloz.to/(neexistujici|smazano|nenalezeno)'
    
    PASSWD_PATTERN = r'<input type="password" class="text" name="file_password" id="frmfilepasswordForm-file_password" />'
    VIPLINK_PATTERN = r'<a href="[^"]*\?disclaimer=1" class="linkVip">'    
    FREE_URL_PATTERN = r'<form name="dwn" action="([^"]+)"'
    PREMIUM_URL_PATTERN = r'<a onclick[^>]*href="([^"]+)[^>]*class="linkVip"'
    CAPTCHA_PATTERN = r'<img style=".*src="([^"]+)" alt="Captcha" class="captcha"'
    CAPTCHA_NB_PATTERN = r'<input class="captcha_nb" type="hidden" name="captcha_nb" value="([0-9]+)" >'

    def process(self, pyfile):
        # check file online
        header = self.load(pyfile.url, just_header=True)
        if "location" in header:
            self.logDebug('LOCATION: ' + header['location'])
            if "utm_source=old" in header['location'] or re.search(self.FILE_OFFLINE_PATTERN, header['location']):
                self.offline()        
        
        self.html = self.load(pyfile.url, decode=True)
        
        # password protected links
        passwords = self.getPassword().splitlines()       
        while self.PASSWD_PATTERN in self.html:
            if passwords:
                password = passwords.pop(0)
                self.logInfo("Password protected link, trying " + password)
                self.html = self.load(pyfile.url, get = {"do": "filepasswordForm-submit"}, post={"file_password": password, "fpwdsend": 'Odeslat'}, cookies=True)
            else:
                self.fail("No or incorrect password")
        
        self.file_info = self.getFileInfo()
                
        # adult content    
        if re.search(self.VIPLINK_PATTERN, self.html):
            self.html = self.load(pyfile.url, get={"disclaimer": "1"})
        
        if self.premium and self.checkTrafficLeft():
            self.handlePremium()
        else: 
            self.handleFree()
            
    def handleFree(self):    
        parsed_url = self.findDownloadURL(premium=False)

        # get and decrypt captcha
        captcha = self.getStorage("captchaUser")
        captcha_nb = self.getStorage("captchaNb")
        captcha_url = "DUMMY"

        if not captcha or not captcha_nb:
            found = re.search(self.CAPTCHA_PATTERN, self.html)
            if not found: self.parseError("CAPTCHA")
            captcha_url = found.group(1)
            
            found = re.search(self.CAPTCHA_NB_PATTERN, self.html)
            if not found: self.parseError("CAPTCHA_NB")
            captcha_nb = found.group(1)
            
            captcha = self.decryptCaptcha(captcha_url)
        
        self.log.debug('CAPTCHA_URL:' + captcha_url + ' CAPTCHA:' + captcha + ' CAPTCHA_NB:' + captcha_nb)

        # download and check        
        self.download(parsed_url, post={"captcha_user": captcha, "captcha_nb": captcha_nb}, cookies=True)
        self.doCheckDownload()   
        
        self.setStorage("captchaUser", captcha)
        self.setStorage("captchaNb", captcha_nb)
    
    def handlePremium(self):
        parsed_url = self.findDownloadURL(premium=True)
        self.download(parsed_url)
        self.doCheckDownload()
        
    def findDownloadURL(self, premium=False):
        msg = "%s link" % ("Premium" if premium else "Free")
        found = re.search(self.PREMIUM_URL_PATTERN if premium else self.FREE_URL_PATTERN, self.html)
        if not found: self.parseError(msg)
        parsed_url = found.group(1)
        self.logDebug("%s: %s" % (msg, parsed_url))
        return parsed_url
    
    def doCheckDownload(self):
        check = self.checkDownload({
            "wrong_captcha": re.compile(self.CAPTCHA_PATTERN),
            "offline": re.compile(self.FILE_OFFLINE_PATTERN),
            "passwd": self.PASSWD_PATTERN
        })

        if check == "wrong_captcha":
            self.delStorage("captchaUser")
            self.delStorage("captchaNb")
            self.invalidCaptcha()
            self.retry(reason="Wrong captcha code")
        elif check == "offline":
            self.offline()
        elif check == "passwd":
            self.fail("Wrong password")

getInfo = create_getInfo(UlozTo)        