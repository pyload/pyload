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
from module.plugins.ReCaptcha import ReCaptcha

class DateiTo(SimpleHoster):
    __name__ = "DateiTo"
    __type__ = "hoster"
    __pattern__ = r"http://(?:www\.)?datei\.to/datei/(?P<ID>\w+)\.html"
    __version__ = "0.01"
    __description__ = """Datei.to plugin - free only"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    FILE_NAME_PATTERN = r'Dateiname:</td>\s*<td colspan="2"><strong>(?P<N>.*?)</'
    FILE_SIZE_PATTERN = r'Dateigr&ouml;&szlig;e:</td>\s*<td colspan="2">(?P<S>.*?)</'
    FILE_OFFLINE_PATTERN = r'>Datei wurde nicht gefunden<|>Bitte wähle deine Datei aus... <'
    PARALELL_PATTERN = r'>Du lädst bereits eine Datei herunter<'
    
    WAIT_PATTERN = r'countdown\({seconds: (\d+)'
    DATA_PATTERN = r'url: "(.*?)", data: "(.*?)",'
    RECAPTCHA_KEY_PATTERN = r'Recaptcha.create\("(.*?)"'
        
    def handleFree(self):
        url = 'http://datei.to/ajax/download.php'
        data = {'P': 'I', 'ID': self.file_info['ID']}
        
        recaptcha = ReCaptcha(self)   
        
        for i in range(10):
            self.logDebug("URL", url, "POST", data)        
            self.html = self.load(url, post = data)
            self.checkErrors()
            
            if url.endswith('download.php') and 'P' in data:
                if data['P'] == 'I':
                    self.doWait()
                    
                elif data['P'] == 'IV':
                    break   
            
            found = re.search(self.DATA_PATTERN, self.html)
            if not found: self.parseError('data')
            url = 'http://datei.to/' + found.group(1)
            data = dict(x.split('=') for x in found.group(2).split('&'))
            
            if url.endswith('recaptcha.php'):
                found = re.search(self.RECAPTCHA_KEY_PATTERN, self.html)
                recaptcha_key = found.group(1) if found else "6LdBbL8SAAAAAI0vKUo58XRwDd5Tu_Ze1DA7qTao"
                
                data['recaptcha_challenge_field'], data['recaptcha_response_field'] = recaptcha.challenge(recaptcha_key) 
        
        else:
            self.fail('Too bad...')  
              
        download_url = self.html
        self.logDebug('Download URL', download_url)
        self.download(download_url)
    
    def checkErrors(self):
        found = re.search(self.PARALELL_PATTERN, self.html)
        if found:
            self.setWait(wait_time + 1, False)
            self.wait(300)
            self.retry()
    
    def doWait(self):                              
        found = re.search(self.WAIT_PATTERN, self.html)
        wait_time = int(found.group(1)) if found else 30
        self.setWait(wait_time + 1, False)
  
        self.load('http://datei.to/ajax/download.php', post = {'P': 'Ads'})
        self.wait()      
        
getInfo = create_getInfo(DateiTo)
