# -*- coding: utf-8 -*-

import re
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo

class OneFichierCom(SimpleHoster):
    __name__ = "OneFichierCom"
    __type__ = "hoster"
    __pattern__ = r"(http://\w+\.((1fichier|d(es)?fichiers|pjointe)\.(com|fr|net|org)|(cjoint|mesfichiers|piecejointe|oi)\.(org|net)|tenvoi\.(com|org|net)|dl4free\.com|alterupload\.com|megadl.fr))"
    __version__ = "0.42"
    __description__ = """1fichier.com download hoster"""
    __author_name__ = ("fragonib", "the-razer", "zoidberg")
    __author_mail__ = ("fragonib[AT]yahoo[DOT]es", "daniel_ AT gmx DOT net", "zoidberg@mujmail.cz")
    
    FILE_NAME_PATTERN = r'">File name :</th>\s*<td>(?P<N>[^<]+)</td>'
    FILE_SIZE_PATTERN = r'<th>File size :</th>\s*<td>(?P<S>[^<])+</td>'
    FILE_OFFLINE_PATTERN = r'The (requested)? file (could not be found|has been deleted)' 
    FILE_URL_REPLACEMENTS = [(r'(http://[^/]*).*', r'\1/en/')]
    
    DOWNLOAD_LINK_PATTERN = r'<br/>&nbsp;<br/>&nbsp;<br/>&nbsp;\s+<a href="(?P<url>http://.*?)"'       
    PASSWORD_PROTECTED_TOKEN = "protected by password"
    WAITING_TOKEN = "Please wait a few seconds"
    
    def handleFree(self):
        if self.WAITING_TOKEN in self.html:
            self.waitAndRetry(60)
        
        # Check for protection 
        if self.isProtected():
            password = self.getPassword()
            self.logDebug("Submitting password [%s]" % password)
            self.download(url, post={"password" : password})
        else:
            downloadLink = self.getDownloadLink()
            self.download(downloadLink)
        
        # Check download 
        self.checkDownloadedFile()
    
    def isProtected(self):
        if self.PASSWORD_PROTECTED_TOKEN in self.html:
            self.logDebug("Links are password protected")
            return True
        return False
        
    def getDownloadLink(self):
        m = re.search(self.DOWNLOAD_LINK_PATTERN, self.html)
        if m is not None:
            url = m.group('url')
            self.logDebug("Got file URL [%s]" % url)
            return url
            
    def checkDownloadedFile(self):
        check = self.checkDownload({"wait": self.WAITING_TOKEN})
        if check == "wait":
            self.waitAndRetry(60)
    
    def waitAndRetry(self, wait_time):
        self.setWait(wait_time, True)
        self.wait()
        self.retry()
        
getInfo = create_getInfo(OneFichierCom)   
