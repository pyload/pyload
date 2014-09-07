# -*- coding: utf-8 -*-
#Testlink:
#http://www.filepup.net/files/a0Gkv71406984663.html
#
import re
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo

class FilepupNet(SimpleHoster):
    __name__ = "FilepupNet"
    __type__ = "hoster"
    __pattern__ = r"https?://(www\.)?filepup.net/files/.*"
    __version__ = "0.01"
    __description__ = """Filepup.net hoster plugin"""
    __author_name__ = ("zapp-brannigan")
    __author_mail__ = ("fuerst.reinje@web.de")
    
    FILE_INFO_PATTERN = r'<strong> <!--class=\"filetitle\"--> (?P<N>.*) </strong><br /> \((?P<S>.*) (?P<U>[kKmM]?i?[bB])\)<!--'
    WAIT_PATTERN = r'var time = ([\d]+);'
    LINK_PATTERN = r"""disabled=\"disabled\" onclick=\"document.location=\'(.*)\';\" /><br/><h3>SLOW SLOT</h3></td>"""
    FILE_OFFLINE_PATTERN = r'<p>This file has been deleted.</p>'
  
    def setup(self):
        self.multiDL = False
        self.chunkLimit = 1
        
    def process(self, pyfile):
        #Load website and set a cookie
        self.html = self.load(pyfile.url, cookies=True, decode=True)
        
        # Wait and press free user button
        try:
            freeuser_link = re.search(self.LINK_PATTERN,self.html).group(1)
            self.logDebug("Final link: "+freeuser_link)
        except:
            self.Fail("Link not found")
        try:
            seconds = re.search(self.WAIT_PATTERN,self.html).group(1)
            self.logDebug("Waiting "+seconds+" seconds")
        except:
            self.logDebug("Waiting seconds not found, will set it to 30")
            seconds = 30
        self.setWait(seconds)
        self.wait()
        a = self.load(freeuser_link, cookies=True, decode=True)
        
        #Start download
        post_data = { "task":"download", "submit":"Download" }
        self.download(freeuser_link, post=post_data, cookies=True)
        check = self.checkDownload({"is_html": re.compile("DOCTYPE html PUBLIC")})
        if check == "is_html":
            self.logInfo("The downloaded file is html, maybe you reached your download limit")
            self.setWait(60*60,True)
            self.wait()
            self.retry()
getInfo = create_getInfo(FilepupNet)
