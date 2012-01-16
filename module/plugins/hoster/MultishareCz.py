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
from random import random
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo

class MultishareCz(SimpleHoster):
    __name__ = "MultishareCz"
    __type__ = "hoster"
    __pattern__ = r"http://(?:\w*\.)?multishare.cz/stahnout/(?P<ID>\d+).*"
    __version__ = "0.40"
    __description__ = """MultiShare.cz"""
    __author_name__ = ("zoidberg")

    FILE_INFO_PATTERN = ur'(?:<li>Název|Soubor): <strong>(?P<N>[^<]+)</strong><(?:/li><li|br)>Velikost: <strong>(?P<S>[^<]+)</strong>'
    FILE_OFFLINE_PATTERN = ur'<h1>Stáhnout soubor</h1><p><strong>Požadovaný soubor neexistuje.</strong></p>'
    FILE_SIZE_REPLACEMENTS = [('&nbsp;', '')]
    
    def process(self, pyfile):
        msurl = re.match(self.__pattern__, pyfile.url)
        if msurl:
            self.fileID = msurl.group('ID')        
            self.html = self.load(pyfile.url, decode = True)       
            self.getFileInfo()
                    
            if self.premium:
                self.handlePremium()
            else:
                self.handleFree()         
        else:     
            self.handleOverriden()           

    def handleFree(self):
        self.download("http://www.multishare.cz/html/download_free.php?ID=%s" % self.fileID)
        
    def handlePremium(self):
        if not self.checkTrafficLeft():
            self.logWarning("Not enough credit left to download file")
            self.resetAccount() 
                
        self.download("http://www.multishare.cz/html/download_premium.php?ID=%s" % self.fileID)
        self.checkTrafficLeft()
    
    def handleOverriden(self):
        if not self.premium: 
            self.fail("Only premium users can download from other hosters")
        
        self.html = self.load('http://www.multishare.cz/html/mms_ajax.php', post = {"link": self.pyfile.url}, decode = True)        
        self.getFileInfo()       
        
        if not self.checkTrafficLeft():
            self.fail("Not enough credit left to download file")
        
        url = "http://dl%d.mms.multishare.cz/html/mms_process.php" % round(random()*10000*random())    
        params = {"u_ID" : self.acc_info["u_ID"], "u_hash" : self.acc_info["u_hash"], "link" : self.pyfile.url}
        self.logDebug(url, params)
        self.download(url, get = params)
        self.checkTrafficLeft()

getInfo = create_getInfo(MultishareCz)