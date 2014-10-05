# -*- coding: utf-8 -*-
#Testlinks:
#http://www.filepup.net/files/k5w4ZVoF1410184283.html
#http://www.filepup.net/files/R4GBq9XH1410186553.html
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
    
    FILE_NAME_PATTERN = r'class="fa fa-play-circle"></i> (?P<N>.*)</h3>'
    FILE_SIZE_PATTERN = r'class="fa fa-archive"></i> \((?P<S>.*) (?P<U>[kKmM]?i?[bB])\)<!--'
    LINK_PATTERN = r"""value=\"DOWNLOAD AS A FREE USER\"  class=\"btn btn-large btn-success btn-rounded\" id=\"dlbutton\" disabled=\"disabled\" onclick=\"document.location=\'(.*)\';\" />"""
  
    def setup(self):
        self.multiDL = False
        self.chunkLimit = 1
        
    def process(self, pyfile):
        self.html = self.load(pyfile.url, cookies=True, decode=True)
        if not '<input type="button" value="Premium Download" class="premium_btn"' in self.html:
            self.offline()
        try:
            freeuser_link = re.search(self.LINK_PATTERN,self.html).group(1)
            self.logDebug("Final link: "+freeuser_link)
        except:
            self.fail("Link not found")
        post_data = { "task":"download" }
        self.download(freeuser_link, post=post_data, cookies=True)
        check = self.checkDownload({"is_html": re.compile("html")})
        if check == "is_html":
            self.fail("The downloaded file is html, the plugin may be out of date")
            
getInfo = create_getInfo(FilepupNet)
