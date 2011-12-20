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
from module.plugins.internal.SimpleHoster import SimpleHoster, parseFileInfo
from module.plugins.ReCaptcha import ReCaptcha
from module.network.RequestFactory import getURL

def replace_eval(js_expr):
    return js_expr.replace(r'eval("', '').replace(r"\'", r"'").replace(r'\"', r'"')

def checkHTMLHeader(url):
    try:
        for i in range(3):
            header = getURL(url, just_header = True)
            for line in header.splitlines():
                line = line.lower()
                if 'location' in line: 
                    url = line.split(':', 1)[1].strip()
                    if 'error.php?errno=320' in url: 
                        return url, 1
                    if not url.startswith('http://'): url = 'http://www.mediafire.com' + url
                    break
                elif 'content-disposition' in line:
                    return url, 2
            else:
               break
    except:
        return url, 3
        
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
    __name__ = "MediafireCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:\w*\.)*mediafire\.com/[^?].*"
    __version__ = "0.70"
    __description__ = """Mediafire.com plugin - free only"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    DOWNLOAD_LINK_PATTERN = r'<div class="download_link"[^>]*z-index:(?P<zindex>\d+)[^>]*>\s*<a href="(?P<href>[^"]+)"'
    JS_KEY_PATTERN = r"DoShow\('mfpromo1'\);\s*((\w+)='';.*?)eval\(\2\);"
    JS_ZMODULO_PATTERN = r"\('z-index'\)\) \% (\d+)\)\);" 
    RECAPTCHA_PATTERN = r'src="http://(?:api.recaptcha.net|www.google.com/recaptcha/api)/challenge\?k=([^"]+)">'
    PAGE1_ACTION_PATTERN = r'<link rel="canonical" href="([^"]+)"/>'
    PASSWORD_PATTERN = r";break;}\s*dh\('"

    FILE_NAME_PATTERN = r'<META NAME="description" CONTENT="(?P<N>[^"]+)"/>'
    FILE_SIZE_PATTERN = r'>Download <span>\((?P<S>[0-9.]+) (?P<U>[kKMG])i?B">\)</span>'
    FILE_OFFLINE_PATTERN = r'class="error_msg_title"> Invalid or Deleted File. </div>'

    def process(self, pyfile):
        self.url, result = checkHTMLHeader(pyfile.url)
        self.logDebug('Location (%d): %s' % (result, self.url))
        
        if result == 0:
            self.html = self.load(self.url, decode = True)
            self.checkCaptcha()
            self.getFileInfo()
            if self.account:
                self.handlePremium()
            else:
                self.handleFree()
        elif result == 1:
            self.offline() 
        else:            
            self.download(self.url, disposition = True)

    def handleFree(self):
        passwords = self.getPassword().split()
        while re.search(self.PASSWORD_PATTERN, self.html):
            if len(passwords):
                password = passwords.pop(0)
                self.logInfo("Password protected link, trying " + password)
                self.html = self.load(self.url, post={"downloadp": password})
            else:
                self.fail("No or incorrect password")
        
        found = re.search(self.JS_KEY_PATTERN, self.html)
        try:
            result = self.js.eval(found.group(1))
            zmodulo = int(re.search(self.JS_ZMODULO_PATTERN, result).group(1))
            self.logDebug("ZMODULO: %d" % zmodulo)
        except Exception, e:
            self.logDebug(e)                                       
            self.retry(3, 0, "Parse error (MODULO)")
        
        vlink = {'zindex': 0, 'href': ''}
        for found in re.finditer(self.DOWNLOAD_LINK_PATTERN, self.html):
            dlink = found.groupdict()
            #self.logDebug(dlink)
            dlink['zindex'] = int(dlink['zindex']) % zmodulo
            if dlink['zindex'] >= vlink['zindex']:
                vlink = dlink
                
        self.logDebug("DOWNLOAD LINK:", vlink)
        self.download(vlink['href'])

    def checkCaptcha(self):
        for i in range(5):
            found = re.search(self.RECAPTCHA_PATTERN, self.html)
            if found:
                captcha_action = re.search(self.PAGE1_ACTION_PATTERN, self.html).group(1)
                captcha_key = found.group(1)
                recaptcha = ReCaptcha(self)
                captcha_challenge, captcha_response = recaptcha.challenge(captcha_key)
                self.html = self.load(captcha_action, post = {
                    "recaptcha_challenge_field": captcha_challenge,
                    "recaptcha_response_field": captcha_response
                    }, decode = True)
            else:
                break
        else:
            self.fail("No valid recaptcha solution received")