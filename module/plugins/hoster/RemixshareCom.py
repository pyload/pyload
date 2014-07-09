# -*- coding: utf-8 -*-
#Testlink:
#http://remixshare.com/download/p946u
#
# The remixshare.com website is very very slow, so
# if your download not starts because of pycurl timeouts:
# Adjust timeouts in /usr/share/pyload/module/network/HTTPRequest.py
#

import re
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo

class RemixshareCom(SimpleHoster):
    __name__ = "RemixshareCom"
    __type__ = "hoster"
    __pattern__ = r"http://remixshare.com/download/.*"
    __version__ = "0.01"
    __description__ = """RemixshareCom Hosterplugin (Supports FREE only)"""
    __author_name__ = ("zapp-brannigan")
    __author_mail__ = ("fuerst.reinje@web.de")
    
    FILE_NAME_PATTERN = r"<span title='.+'>(?P<N>.+)</span><span class.*"
    FILE_SIZE_PATTERN = r"""<span class='light2'>&nbsp;\((?P<S>[0-9]+\.*[0-9]*)&nbsp;(?P<U>[kKmMbB]*)\)"""
    FILE_OFFLINE_PATTERN = r'<h1>Ooops!</h1>'
    WAIT_PATTERN = r"var XYZ = \"(\d+)\""
    FILE_URL_PATTERN = r'.+(?P<url>http://remixshare.com/downloadfinal/.+)"\+.+'
    FILE_TOKEN_PATTERN = r'var acc = (?P<token>[0-9]+).+'
    
    def setup(self):
        self.multiDL = True
        self.chunkLimit = 1
        
    def process(self, pyfile):
        self.html = self.load(pyfile.url, decode=True)
        
        #Find URL and token
        b = re.search(self.FILE_URL_PATTERN,self.html)
        if b is None:
            self.fail("Can not parse download url")
        c = re.search(self.FILE_TOKEN_PATTERN,self.html)
        if c is None:
            self.fail("Can not parse file token")
        dl_url = b.group(1) + c.group(1)
        
        #Check if we have to wait
        seconds = re.search(self.WAIT_PATTERN,self.html)
        if seconds is not None:
            self.logDebug("Waitingtime: " + seconds.group(1))
            self.logDebug("Download-URL: " + dl_url)
            self.logDebug("Waiting now...")
            self.setWait(seconds.group(1))
            self.wait()
        
        # Finally start downloading...
        self.logDebug("Start download")
        self.download(dl_url,disposition=True)
        
getInfo = create_getInfo(RemixshareCom)
