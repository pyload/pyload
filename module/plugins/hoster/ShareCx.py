#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from module.plugins.Hoster import Hoster
from module.plugins.Plugin import chunks
from module.network.Request import getURL
#from module.BeautifulSoup import BeautifulSoup

def getInfo(urls):
    api_url = "http://www.share.cx/uapi?do=check&links="
    
    for chunk in chunks(urls, 90):
        get = ""
        for url in chunk:
            get += ";"+url
            
        api = getURL(api_url+get[1:])
        result = []
        
        for i, link in enumerate(api.split()):
            url,name,size = link.split(";")
            if name and size:
                status = 2
            else:
                status = 1
                
            if not name: name = chunk[i]
            if not size: size = 0
                
            result.append( (name, size, status, chunk[i]) )
        
        yield result

class ShareCx(Hoster):
    __name__ = "ShareCx"
    __type__ = "hoster"
    __pattern__ = r"http://[\w\.]*?share\.cx/(files|videos)/\d+"
    __version__ = "0.1"
    __description__ = """Share.cx Download Hoster"""
    __author_name__ = ("jeix")
    __author_mail__ = ("jeix@hasnomail.de")
        
        
    def setup(self):
        self.multiDL = False
        
        
    def process(self, pyfile):
        self.pyfile = pyfile
        self.download_html()
        if not self.file_exists():
            self.offline()
            
        pyfile.name = self.get_file_name()
        self.doDownload()
        
        
    def download_html(self):
        self.html = self.load(self.pyfile.url)

    def doDownload(self):
        """ returns the absolute downloadable filepath
        """
        if self.html is None:
            self.download_html()

        op          = re.search(r'name="op" value="(.*?)"', self.html).group(1)
        usr_login   = re.search(r'name="usr_login" value="(.*?)"', self.html).group(1)
        id          = re.search(r'name="id" value="(.*?)"', self.html).group(1)
        fname       = re.search(r'name="fname" value="(.*?)"', self.html).group(1)
        referer     = re.search(r'name="referer" value="(.*?)"', self.html).group(1)
        method_free = "Datei+herunterladen"
        
        self.html   = self.load(self.pyfile.url, post={
                "op" : op,
                "usr_login" : usr_login,
                "id" : id,
                "fname" : fname,
                "referer" : referer,
                "method_free" : method_free
            })
            
            
        m = re.search(r'startTimer\((\d+)\)', self.html)
        if m is not None:
            wait_time = int(m.group(1))
            self.setWait(wait_time)
            self.wantReconnect = True
            self.log.debug("%s: IP blocked wait %d seconds." % (self.__name__, wait_time))
            self.wait()
            
        m = re.search(r'countdown">.*?(\d+).*?</span>', self.html)
        if m is None:
            m = re.search(r'id="countdown_str".*?<span id=".*?">.*?(\d+).*?</span', self.html)
        if m is not None:
            wait_time = int(m.group(1))
            self.setWait(wait_time)
            self.wantReconnect = False
            self.log.debug("%s: Waiting %d seconds." % (self.__name__, wait_time))
            self.wait()

        
        op = re.search(r'name="op" value="(.*?)"', self.html).group(1)
        id = re.search(r'name="id" value="(.*?)"', self.html).group(1)
        rand = re.search(r'name="rand" value="(.*?)"', self.html).group(1)
        referer = re.search(r'name="referer" value="(.*?)"', self.html).group(1)
        method_free = re.search(r'name="method_free" value="(.*?)"', self.html).group(1)
        method_premium = re.search(r'name="method_premium" value="(.*?)"', self.html).group(1)
        down_script = re.search(r'name="down_script" value="(.*?)"', self.html).group(1)

        data = {
            "op" : op,
            "id" : id,
            "rand" : rand,
            "referer" : referer,
            "method_free" : method_free,
            "method_premium" : method_premium,
            "down_script" : down_script
        }
        
        if '/captchas/' in self.html:
            captcha_url = re.search(r'(http://(?:[\w\d]+\.)?.*?/captchas/.*?)', self.html).group(1)
            captcha = self.decryptCaptcha(captcha_url)
            data["code"] = captcha
            

        self.download(self.pyfile.url, post=data)

        # soup = BeautifulSoup(html)
        # form = soup.find("form")
        # postfields = {}
        # for input in form,findall("input"):
           # postfields[input["name"]] = input["value"]
        # postfields["method_free"] = "Datei herunterladen"
    
    def get_file_name(self):
        if self.html is None:
            self.download_html()
            
        name = re.search(r'alt="Download" /></span>(.*?)</h3>', self.html).group(1)
        return name

    def file_exists(self):
        """ returns True or False
        """
        if self.html is None:
            self.download_html()
        
        if re.search(r'File not found<br>It was deleted due to inactivity or abuse request', self.html) is not None:
            return False

        return True
            
            
