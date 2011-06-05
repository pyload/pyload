# -*- coding: utf-8 -*-

import re

from module.plugins.Hoster import Hoster
from module.network.RequestFactory import getURL


def getInfo(urls):
    result = []
    
    for url in urls:
        
        # Get file info html
        id = re.match(OneFichierCom.__pattern__, url).group('id')
        url = 'http://%s.1fichier.com/en' % id  # Force response in english
        html = getURL(url) 
        
        # Offline?
        if re.search(OneFichierCom.FILE_OFFLINE_PATTERN, html):
            result.append((url, 0, 1, url))
            continue
        
        # Name
        for pattern in OneFichierCom.FILE_NAME_PATTERNS:
            m = re.search(pattern, html)
            if m is not None:
                name = m.group('name').strip()
        
        # Size
        m = re.search(OneFichierCom.FILE_SIZE_PATTERN, html)
        value = float(m.group('size'))
        units = m.group('units')[0].upper()
        pow = {'K' : 1, 'M' : 2, 'G' : 3}[units] 
        size = int(value*1024**pow)
    
        # Return info
        result.append((name, size, 2, url))
        
    yield result


class OneFichierCom(Hoster):
    __name__ = "OneFichierCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?P<id>[a-z0-9]+)\.1fichier\.com(?P<remain>.*)"
    __version__ = "0.3"
    __description__ = """1fichier.com download hoster"""
    __author_name__ = ("fragonib")
    __author_mail__ = ("fragonib[AT]yahoo[DOT]es")
    
    FILE_NAME_PATTERNS = (
        r'">File name :</th>[\t\r\n ]+<td>(?P<name>.*?)</td>',
        r">Click here to download (?P<name>.*?)</a>",
        r"content=\"Download the file named (?P<name>.*?)\">", 
        r"<title>Download the file\s*:\s*(?P<name>.*?)</title>"
    )
    FILE_SIZE_PATTERN = r"<th>File size :</th>\s+<td>(?P<size>[\d\.]*) (?P<units>\w+)</td>"
    DOWNLOAD_LINK_PATTERN = r'<br/>&nbsp;<br/>&nbsp;<br/>&nbsp;\s+<a href="(?P<url>http://.*?)"'
    FILE_OFFLINE_PATTERN = r"(The requested file could not be found|The file may has been deleted by its owner)"
    PASSWORD_PROTECTED_TOKEN = "protected by password"
    WAITING_TOKEN = "Please wait a few seconds"

    def setup(self):
        self.html = None
        self.multiDL = False

    def process(self, pyfile):

        # Get main page (english version)
        url = self.getEnglishURL()
        self.html = self.load(url)  
        self.handleErrors()
        
        # Get file info
        pyfile.name = self.getFileName()
        pyfile.size = self.getFileSize()
        
        # Check for protection 
        if self.isProtected():
            password = self.getPassword()
            self.logDebug("Submitting password [%s]" % password)
            self.download(url, post={"password" : password})
        else:
            downloadLink = self.getDownloadLink()
            self.download(downloadLink)
        
        # Check download 
        self.handleDownloadedFile()

    def getEnglishURL(self):
        id = re.match(self.__pattern__, self.pyfile.url).group('id')
        url = 'http://%s.1fichier.com/en' % id
        return url

    def getFileName(self):
        for pattern in self.FILE_NAME_PATTERNS:
            m = re.search(pattern, self.html)
            if m is not None:
                name = m.group('name').strip()
                self.logDebug("Got file name [%s]" % name)
                return name
            
    def getFileSize(self):
        m = re.search(self.FILE_SIZE_PATTERN, self.html) 
        if m is not None:
            size = float(m.group('size'))
            units = m.group('units')[0].upper()
            try:
                multiplier = 1024 ** {"K":1, "M":2, "G":3}[units]
            except KeyError:
                multiplier = 1
            bytes = int(size * multiplier)
            self.logDebug("Got file size of [%s] bytes" % bytes)
            return bytes
    
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
        
    def handleErrors(self):
        if re.search(self.FILE_OFFLINE_PATTERN, self.html) is not None:
            self.logDebug("File not yet available.")
            self.offline()
            
    def handleDownloadedFile(self):
        check = self.checkDownload({"wait": self.WAITING_TOKEN})
        if check == "wait":
            wait = 5
            self.setWait(wait, True)
            self.wait()
            self.retry()