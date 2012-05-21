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

class UploadheroCom(SimpleHoster):
    __name__ = "UploadheroCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:www\.)?uploadhero\.com/dl/\w+"
    __version__ = "0.12"
    __description__ = """UploadHero.com plugin"""
    __author_name__ = ("mcmyst", "zoidberg")
    __author_mail__ = ("mcmyst@hotmail.fr", "zoidberg@mujmail.cz")

    SH_COOKIES = [("http://uploadhero.com", "lang", "en")]
    FILE_NAME_PATTERN = r'<div class="nom_de_fichier">(?P<N>.*?)</div>'
    FILE_SIZE_PATTERN = r'Taille du fichier : </span><strong>(?P<S>.*?)</strong>'
    FILE_OFFLINE_PATTERN = r'<p class="titre_dl_2">|<div class="raison"><strong>Le lien du fichier ci-dessus n\'existe plus.'
    
    DOWNLOAD_URL_PATTERN = r'<a href="([^"]+)" id="downloadnow"'
    
    IP_BLOCKED_PATTERN = r'href="(/lightbox_block_download.php\?min=.*?)"'
    IP_WAIT_PATTERN = r'<span id="minutes">(\d+)</span>.*\s*<span id="seconds">(\d+)</span>'

    CAPTCHA_PATTERN = r'"(/captchadl\.php\?[a-z0-9]+)"'
    FREE_URL_PATTERN = r'var magicomfg = \'<a href="(http://[^<>"]*?)"|"(http://storage\d+\.uploadhero\.com/\?d=[A-Za-z0-9]+/[^<>"/]+)"'
    
    def handleFree(self):
        self.checkErrors() 
        
        found = re.search(self.CAPTCHA_PATTERN, self.html)
        if not found: self.parseError("Captcha URL")
        captcha_url = "http://uploadhero.com" + found.group(1)
                      
        for i in range(5):
            captcha = self.decryptCaptcha(captcha_url)    
            self.html = self.load(self.pyfile.url, get = {"code": captcha})
            found = re.search(self.FREE_URL_PATTERN, self.html) 
            if found:
                self.correctCaptcha()
                download_url = found.group(1) or found.group(2)
                break
            else:
                self.invalidCaptcha()
        else:
            self.fail("No valid captcha code entered")                  
        
        self.download(download_url)
    
    def handlePremium(self):
        self.log.debug("%s: Use Premium Account" % self.__name__)
        self.html = self.load(self.pyfile.url)
        link = re.search(self.DOWNLOAD_URL_PATTERN, self.html).group(1)
        self.log.debug("Downloading link : '%s'" % link)
        self.download(link) 
             
    def checkErrors(self):
        found = re.search(self.IP_BLOCKED_PATTERN, self.html)
        if found:
            self.html = self.load("http://uploadhero.com%s" % found.group(1))
                    
            found = re.search(self.IP_WAIT_PATTERN, self.html)
            wait_time = (int(found.group(1)) * 60 + int(found.group(2))) if found else 300
            self.setWait(wait_time, True)
            self.wait()
            self.retry()
        
getInfo = create_getInfo(UploadheroCom)