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
from module.plugins.Crypter import Crypter

class LinkdecrypterCom(Crypter):
    __name__ = "LinkdecrypterCom"
    __type__ = "crypter"
    __version__ = "0.24"
    __description__ = """linkdecrypter.com"""
    __author_name__ = ("zoidberg", "flowlee")
    
    TEXTAREA_PATTERN = r'<textarea name="links" wrap="off" readonly="1" class="caja_des">(.+)</textarea>'
    PASSWORD_PATTERN = r'<p class="textog" style="color:red"><b>PASSWORD:</b></p>'
    CAPTCHA_PATTERN = r'<img style="cursor:crosshair;" src="([^"]+)" alt="Loading CAPTCHA...">'
    REDIR_PATTERN = r'<i>(Click <a href="./">here</a> if your browser does not redirect you).</i>'
    
    def decrypt(self, pyfile):

        self.passwords = self.getPassword().splitlines()
        
        new_links = self.decryptAPI() or self.decryptHTML()                
        if new_links:
            self.core.files.addLinks(new_links, self.pyfile.package().id)
        else:
            self.fail('Could not extract any links')    

    def decryptAPI(self):
            
        get_dict = { "t": "link", "url": self.pyfile.url, "lcache": "1" } 
        self.html = self.load('http://linkdecrypter.com/api', get = get_dict)
        if self.html.startswith('http://'): return self.html.splitlines()
        
        if self.html == 'INTERRUPTION(PASSWORD)':
            for get_dict['pass'] in self.passwords:
                self.html = self.load('http://linkdecrypter.com/api', get= get_dict)
                if self.html.startswith('http://'): return self.html.splitlines()                                                
        
        self.logError('API', self.html)
        if self.html == 'INTERRUPTION(PASSWORD)':
            self.fail("No or incorrect password")
        
        return None                   
            
    def decryptHTML(self):
        
        self.html = self.load('http://linkdecrypter.com', cookies = True)        
        links_sessid = "links" + self.req.cj.getCookie("PHPSESSID")
        retries = 5
        
        post_dict = { "link_cache": "on", links_sessid: self.pyfile.url, "modo_links": "text" }                                              
        self.html = self.load('http://linkdecrypter.com', post = post_dict, cookies = True)
        
        while self.passwords or retries:                                    
            found = re.search(self.TEXTAREA_PATTERN, self.html, flags=re.DOTALL)                    
            if found: return [ x for x in found.group(1).splitlines() if '[LINK-ERROR]' not in x ]
                                             
            found = re.search(self.CAPTCHA_PATTERN, self.html)
            if found:
                self.logInfo("Captcha protected link")
                captcha = self.decryptCaptcha(url='http://linkdecrypter.com/' + found.group(1))
                self.html = self.load('http://linkdecrypter.com', post={ "captcha": captcha })
                retries -= 1
                
            elif self.PASSWORD_PATTERN in self.html:
                if self.passwords:
                    password = self.passwords.pop(0)
                    self.logInfo("Password protected link, trying " + password)
                    self.html = self.load('http://linkdecrypter.com', post= {'password': password})
                else:
                    self.fail("No or incorrect password")
            
            else:
                retries -= 1            
                self.html = self.load('http://linkdecrypter.com', cookies = True)
        
        return None                           