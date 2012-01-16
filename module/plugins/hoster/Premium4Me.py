#!/usr/bin/env python
# -*- coding: utf-8 -*-

from urllib import quote
from module.plugins.Hoster import Hoster

class Premium4Me(Hoster):
    __name__ = "Premium4Me"
    __version__ = "0.10"
    __type__ = "hoster"

    __pattern__ = r"http://premium4.me/.*"
    __description__ = """premium4.me hoster plugin"""
    __author_name__ = ("RaNaN", "zoidberg")
    __author_mail__ = ("RaNaN@pyload.org", "zoidberg@mujmail.cz")

    def setup(self):
        self.resumeDownload = True
        self.chunkLimit = 1

    def process(self, pyfile):
        if not self.account:
            self.logError(_("Please enter your premium4.me account or deactivate this plugin"))
            self.fail("No premium4.me account provided")

        self.logDebug("premium4.me: Old URL: %s" % pyfile.url)

        tra = self.getTraffic()
        
        #raise timeout to 2min
        self.req.setOption("timeout", 120)
        
        self.download("http://premium4.me/api/getfile.php?authcode=%s&link=%s" % (self.account.authcode, quote(pyfile.url, "")), disposition=True)
        
        err = ''       
        if self.req.http.code == '420':
            # Custom error code send - fail
            lastDownload = fs_encode(self.lastDownload)
            
            if exists(lastDownload): 
                f = open(lastDownload, "rb")
                err = f.read(256).strip()
                f.close()
                remove(lastDownload)
            else:
                err = 'File does not exist'
        
        trb = self.getTraffic()
        self.logInfo("Filesize: %d, Traffic used %d, traffic left %d" % (pyfile.size, tra-trb, trb))
                    
        if err: self.fail(err)
        
    def getTraffic(self):
        try:
            traffic = int(self.load ("http://premium4.me/api/traffic.php?authcode=%s" % self.account.authcode))
        except:
            traffic = 0 
        return traffic       