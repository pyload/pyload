#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re, subprocess, tempfile, os
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo, timestamp
from module.plugins.ReCaptcha import ReCaptcha
from module.common.json_layer import json_loads

class ZippyshareCom(SimpleHoster):
    __name__ = "ZippyshareCom"
    __type__ = "hoster"
    __pattern__ = r"(?P<HOST>http://www\d{0,2}\.zippyshare.com)/v(?:/|iew.jsp.*key=)(?P<KEY>\d+)"
    __version__ = "0.33"
    __description__ = """Zippyshare.com Download Hoster"""
    __author_name__ = ("spoob", "zoidberg")
    __author_mail__ = ("spoob@pyload.org", "zoidberg@mujmail.cz")
    
    FILE_NAME_PATTERN = r'>Name:</font>\s*<font [^>]*>(?P<N>[^<]+)</font><br />'
    FILE_SIZE_PATTERN = r'>Size:</font>\s*<font [^>]*>(?P<S>[0-9.,]+) (?P<U>[kKMG]+)i?B</font><br />'
    FILE_OFFLINE_PATTERN = r'>File does not exist on this server</div>'

    DOWNLOAD_URL_PATTERN = r">([^<>]*)document\.getElementById\('dlbutton'\).href = ([^;]+);"
    SEED_PATTERN = r'swfobject.embedSWF\("([^"]+)".*?seed: (\d+)'
    CAPTCHA_KEY_PATTERN = r'Recaptcha.create\("([^"]+)"'
    CAPTCHA_SHORTENCODE_PATTERN = r"shortencode: '([^']+)'"
    CAPTCHA_DOWNLOAD_PATTERN = r"document.location = '([^']+)'"
    
    LAST_KNOWN_VALUES = (1, 1424574) #time = (seed * multimply) % modulo

    def setup(self):
        self.html = None
        self.wantReconnect = False
        self.multiDL = True

    def handleFree(self): 
        url = self.get_file_url()
        if not url: self.fail("Download URL not found.")
        self.logDebug("Download URL %s" % url)
        self.download(url, cookies = True)
        
        check = self.checkDownload({
            "swf_values": re.compile(self.SEED_PATTERN)
        })

        if check == "swf_values":
            swf_sts = self.getStorage("swf_sts")            
            if not swf_sts:
                self.setStorage("swf_sts", 2)
                self.setStorage("swf_stamp", 0)
            elif swf_sts == '1':
                self.setStorage("swf_sts", 2)
                    
            self.retry(max_tries = 1)  
        
    def get_file_url(self):
        """ returns the absolute downloadable filepath
        """
        url = multiply = modulo = None

        found = re.search(self.DOWNLOAD_URL_PATTERN, self.html, re.S)
        if found:
            #Method #1: JS eval
            self.logDebug("JS", found.groups())
            url = self.js.eval("%s%s" % (found.group(1), found.group(2)))
        else:
            #Method #2: SWF eval
            seed_search = re.search(self.SEED_PATTERN, self.html)
            if seed_search:
                swf_url, file_seed = seed_search.groups()
                
                swf_sts = self.getStorage("swf_sts")
                swf_stamp = int(self.getStorage("swf_stamp") or 0)
                self.logDebug("SWF", swf_sts, swf_stamp)
                            
                if not swf_sts:
                    self.logDebug('Using default values')
                    multiply, modulo = self.LAST_KNOWN_VALUES
                elif swf_sts == "1":
                    self.logDebug('Using stored values') 
                    multiply = self.getStorage("multiply")
                    modulo = self.getStorage("modulo")
                elif swf_sts == "2" and (swf_stamp + 3600000) < timestamp():
                    multiply, modulo = self.get_swf_values(self.file_info['HOST'] + swf_url)                  
                    
                if multiply and modulo:
                    self.logDebug("TIME = (%s * %s) %s" % (file_seed, multiply, modulo)) 
                    url = "/download?key=%s&time=%d" % (self.file_info['KEY'], (int(file_seed) * int(multiply)) % int(modulo))
                    
            if not url:
                #Method #3: Captcha
                url = self.do_recaptcha()
                               
        return self.file_info['HOST'] + url
        
    def get_swf_values(self, swf_url):
        self.logDebug('Parsing values from %s' % swf_url)
        multiply = modulo = None                         
        
        fd, fpath = tempfile.mkstemp()
        try:
            swf_data = self.load(swf_url)
            os.write(fd, swf_data)
           
            p = subprocess.Popen(['swfdump', '-a', fpath], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = p.communicate()
            
            if err:
                self.logError(err)
            else:
                m_str = re.search(r'::break.*?{(.*?)}', out, re.S).group(1)
                multiply = re.search(r'pushbyte (\d+)', m_str).group(1)
                modulo = re.search(r'pushint (\d+)', m_str).group(1)
        finally:
            os.close(fd) 
            os.remove(fpath)
        
        if multiply and modulo:
            self.setStorage("multiply", multiply)
            self.setStorage("modulo", modulo)
            self.setStorage("swf_sts", 1)
        else:
            self.logError("Parsing SWF failed: swfdump not installed or plugin out of date")
            self.setStorage("swf_sts", 2)
            
        self.setStorage("swf_stamp", timestamp())              
        
        return multiply, modulo
             
    def do_recaptcha(self):
        self.logDebug('Trying to solve captcha')
        captcha_key = re.search(self.CAPTCHA_KEY_PATTERN, self.html).group(1)
        shortencode = re.search(self.CAPTCHA_SHORTENCODE_PATTERN, self.html).group(1)
        url = re.search(self.CAPTCHA_DOWNLOAD_PATTERN, self.html).group(1)        
        
        recaptcha = ReCaptcha(self)

        for i in range(5):
            challenge, code = recaptcha.challenge(captcha_key)

            response = json_loads(self.load(self.file_info['HOST'] + '/rest/captcha/test',
                            post={'challenge': challenge,
                                  'response': code,
                                  'shortencode': shortencode}))
            self.logDebug("reCaptcha response : %s" % response)
            if response == True:
                self.correctCaptcha
                break
            else:
                self.invalidCaptcha()
        else: self.fail("Invalid captcha")
        
        return url               

getInfo = create_getInfo(ZippyshareCom)