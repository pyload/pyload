# -*- coding: utf-8 -*-
from module.network.RequestFactory import getURL
from module.plugins.Hoster import Hoster
from module.plugins.ReCaptcha import ReCaptcha
from module.utils import parseFileSize
from module.plugins.Plugin import chunks
from module.common.json_layer import json_loads

import re

def checkFile(plugin, urls):
    file_info = []
    url_dict = {}
    
    for url in urls:
        url_dict[re.search(plugin.__pattern__, url).group('id')] = (url, 0, 0, url)
    url_ids = url_dict.keys()
    urls = map(lambda url_id: 'http://www.filefactory.com/file/' + url_id, url_ids)

    html = getURL("http://www.filefactory.com/tool/links.php", post = {"func": "links", "links": "\n".join(urls)}, decode=True)   
        
    for m in re.finditer(plugin.LC_INFO_PATTERN, html):
        if m.group('id') in url_ids:
            url_dict[m.group('id')] = (m.group('name'), parseFileSize(m.group('size')), 2, url_dict[m.group('id')][3])
            
    for m in re.finditer(plugin.LC_OFFLINE_PATTERN, html):
        if m.group('id') in url_ids:
            url_dict[m.group('id')] = (url_dict[m.group('id')][0], 0, 1, url_dict[m.group('id')][3])
    
    file_info = url_dict.values()
    
    return file_info
   
class FilefactoryCom(Hoster):
    __name__ = "FilefactoryCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:www\.)?filefactory\.com/file/(?P<id>[a-zA-Z0-9]+).*" # URLs given out are often longer but this is the requirement
    __version__ = "0.34"
    __description__ = """Filefactory.Com File Download Hoster"""
    __author_name__ = ("paulking", "zoidberg")
    
    LC_INFO_PATTERN = r'<h1 class="name">(?P<name>[^<]+) \((?P<size>[0-9.]+ \w+)\)</h1>\s*<p>http://www.filefactory.com/file/(?P<id>\w+)/'
    LC_OFFLINE_PATTERN = r'<p>http://www.filefactory.com/file/(?P<id>\w+)/</p>\s*<p class="errorResponse">'
 
    FILE_OFFLINE_PATTERN = r'<title>File Not Found'
    FILE_NAME_PATTERN = r'<span class="last">(?P<name>.*?)</span>'
    FILE_INFO_PATTERN = r'<span>(?P<size>\d(\d|\.)*) (?P<units>..) file uploaded'
    
    FILE_CHECK_PATTERN = r'check:\s*\'(?P<check>.*?)\''
    CAPTCHA_KEY_PATTERN = r'Recaptcha.create\(\s*"(.*?)",' 
    WAIT_PATTERN = r'id="startWait" value="(?P<wait>\d+)"'
    FILE_URL_PATTERN = r'<p[^>]*?id="downloadLinkTarget"[^>]*>\s*<a href="(?P<url>.*?)"' 
            
    def setup(self):
        self.multiDL = self.resumeDownloads = self.premium

    def process(self, pyfile):
        # Check file
        pyfile.name, pyfile.size, status, self.url = checkFile(self, [pyfile.url])[0]     
        if status != 2: self.offline()
        self.logDebug("File Name: %s Size: %d" % (pyfile.name, pyfile.size)) 
        
        # Handle downloading
        url = self.checkDirectDownload(pyfile.url)
        if url:
            self.download(url)
        else:                
            self.html = self.load(pyfile.url, decode = True)
                      
            if self.premium:
                self.handlePremium()
            else:
                self.handleFree()
              
    def checkDirectDownload(self, url):
        for i in range(5):
            header = self.load(url, just_header = True)           
            if 'location' in header:
                url = header['location'].strip() 
                if not url.startswith("http://"):
                    url = "http://www.filefactory.com" + url
                self.logDebug('URL: ' + url)
            elif 'content-disposition' in header:
                return url
        
        return False                                
    
    def handleFree(self):
        if "Currently only Premium Members can download files larger than" in self.html:
            self.fail("File too large for free download")
        elif "All free download slots on this server are currently in use" in self.html:
            self.retry(50, 900, "All free slots are busy")
             
        # Check Id
        self.check = re.search(self.FILE_CHECK_PATTERN, self.html).group('check')
        self.logDebug("File check code is [%s]" % self.check)
        
        # Resolve captcha
        found = re.search(self.CAPTCHA_KEY_PATTERN, self.html)
        recaptcha_key = found.group(1) if found else "6LeN8roSAAAAAPdC1zy399Qei4b1BwmSBSsBN8zm"
        recaptcha = ReCaptcha(self)
        
        # Try up to 5 times
        for i in range(5):           
            challenge, code = recaptcha.challenge(recaptcha_key)
            response = json_loads(self.load("http://www.filefactory.com/file/checkCaptcha.php",
                            post={"check" : self.check, "recaptcha_challenge_field" : challenge, "recaptcha_response_field" : code}))
            if response['status'] == 'ok':
                self.correctCaptcha()
                break
            else:
                self.invalidCaptcha()                            
        else:
            self.fail("No valid captcha after 5 attempts")
        
        # This will take us to a wait screen
        waiturl = "http://www.filefactory.com" + response['path']
        self.logDebug("Fetching wait with url [%s]" % waiturl)
        waithtml = self.load(waiturl, decode=True)

        # Find the wait value and wait     
        wait = int(re.search(self.WAIT_PATTERN, waithtml).group('wait'))
        self.logDebug("Waiting %d seconds." % wait)
        self.setWait(wait, True)
        self.wait()

        # Now get the real download url and retrieve the file
        url = re.search(self.FILE_URL_PATTERN,waithtml).group('url')
        # this may either download our file or forward us to an error page
        self.logDebug("Download URL: %s" % url)
        dl = self.download(url)
        
        check = self.checkDownload({"multiple": "You are currently downloading too many files at once.",
                                    "error": '<div id="errorMessage">'})

        if check == "multiple":
            self.setWait(15*60)
            self.logDebug("Parallel downloads detected; waiting 15 minutes")
            self.wait()
            self.retry()
        elif check == "error":
            self.fail("Unknown error")
    
    def handlePremium(self):
        self.fail('Please enable direct downloads')
        
def getInfo(urls):
    for chunk in chunks(urls, 100): yield checkFile(FilefactoryCom, chunk)
