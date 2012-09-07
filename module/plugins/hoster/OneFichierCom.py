# -*- coding: utf-8 -*-

import re
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo

class OneFichierCom(SimpleHoster):
    __name__ = "OneFichierCom"
    __type__ = "hoster"
    __pattern__ = r"(http://(\w+)\.((1fichier|d(es)?fichiers|pjointe)\.(com|fr|net|org)|(cjoint|mesfichiers|piecejointe|oi)\.(org|net)|tenvoi\.(com|org|net)|dl4free\.com|alterupload\.com|megadl.fr))"
    __version__ = "0.44"
    __description__ = """1fichier.com download hoster"""
    __author_name__ = ("fragonib", "the-razer", "zoidberg")
    __author_mail__ = ("fragonib[AT]yahoo[DOT]es", "daniel_ AT gmx DOT net", "zoidberg@mujmail.cz")
    
    FILE_NAME_PATTERN = r'">File name :</th>\s*<td>(?P<N>[^<]+)</td>'
    FILE_SIZE_PATTERN = r'<th>File size :</th>\s*<td>(?P<S>[^<]+)</td>'
    FILE_OFFLINE_PATTERN = r'The (requested)? file (could not be found|has been deleted)' 
    FILE_URL_REPLACEMENTS = [(r'(http://[^/]*).*', r'\1/en/')]
    
    DOWNLOAD_LINK_PATTERN = r'<br/>&nbsp;<br/>&nbsp;<br/>&nbsp;\s+<a href="(?P<url>http://.*?)"'       
    PASSWORD_PROTECTED_TOKEN = "protected by password"
    WAITING_PATTERN = "you must wait (\d+) minutes"
    
    def process(self, pyfile):
        found = re.search(self.__pattern__, pyfile.url)
        file_id = found.group(2)      
        url = "http://%s.%s/en/" % (found.group(2), found.group(3))         
        self.html = self.load(url, decode = True)
        
        found = re.search(self.WAITING_PATTERN, self.html)
        if found:
            self.waitAndRetry(int(found.group(1)) * 60)
        
        self.getFileInfo()
        
        url, inputs = self.parseHtmlForm('action="http://%s' % file_id)
        if not url or not inputs:
            self.parseError("Download link not found")
        
        # Check for protection 
        if "pass" in inputs:
            inputs['pass'] = self.getPassword()
            
        self.download(url, post = inputs)
        
        # Check download 
        self.checkDownloadedFile()
            
    def checkDownloadedFile(self):
        check = self.checkDownload({"wait": self.WAITING_PATTERN})
        if check == "wait":
            self.waitAndRetry(int(self.lastcheck.group(1)) * 60)
    
    def waitAndRetry(self, wait_time):
        self.setWait(wait_time, True)
        self.wait()
        self.retry()
        
getInfo = create_getInfo(OneFichierCom)   
