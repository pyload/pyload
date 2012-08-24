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
    __version__ = "0.26"
    __description__ = """linkdecrypter.com"""
    __author_name__ = ("zoidberg", "flowlee")
    
    TEXTAREA_PATTERN = r'<textarea name="links" wrap="off" readonly="1" class="caja_des">(.+)</textarea>'
    PASSWORD_PATTERN = r'<input type="text" name="password"'
    CAPTCHA_PATTERN = r'<img class="captcha" src="(.+?)"(.*?)>'
    REDIR_PATTERN = r'<i>(Click <a href="./">here</a> if your browser does not redirect you).</i>'
    
    def decrypt(self, pyfile):

        self.passwords = self.getPassword().splitlines()
        
        # API not working anymore
        new_links = self.decryptHTML()                
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

        retries = 5
        
        post_dict = { "link_cache": "on", "pro_links": self.pyfile.url, "modo_links": "text" }                                              
        self.html = self.load('http://linkdecrypter.com/', post = post_dict, cookies = True)
        
        while self.passwords or retries:                                    
            found = re.search(self.TEXTAREA_PATTERN, self.html, flags=re.DOTALL)                    
            if found: return [ x for x in found.group(1).splitlines() if '[LINK-ERROR]' not in x ]
                                             
            found = re.search(self.CAPTCHA_PATTERN, self.html)
            if found:
                captcha_url = 'http://linkdecrypter.com/' + found.group(1)
                result_type = "positional" if "getPos" in found.group(2) else "textual"
                
                found = re.search(r"<p><i><b>([^<]+)</b></i></p>", self.html)
                msg = found.group(1) if found else ""
                self.logInfo("Captcha protected link", result_type, msg)
                
                captcha = self.decryptCaptcha(captcha_url, result_type = result_type)
                if result_type == "positional":
                    captcha = "%d|%d" % captcha
                self.html = self.load('http://linkdecrypter.com/', post={ "captcha": captcha })
                retries -= 1
                
            elif self.PASSWORD_PATTERN in self.html:
                if self.passwords:
                    password = self.passwords.pop(0)
                    self.logInfo("Password protected link, trying " + password)
                    self.html = self.load('http://linkdecrypter.com/', post= {'password': password})
                else:
                    self.fail("No or incorrect password")
            
            else:
                retries -= 1            
                self.html = self.load('http://linkdecrypter.com/', cookies = True)
        
        return None                           