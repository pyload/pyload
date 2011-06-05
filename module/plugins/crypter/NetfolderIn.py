# -*- coding: utf-8 -*-

from module.plugins.Crypter import Crypter
import re

class NetfolderIn(Crypter):
    __name__ = "NetfolderIn"
    __type__ = "crypter"
    __pattern__ = r"http://(?:www\.)?netfolder.in/((?P<id1>\w+)/\w+|folder.php\?folder_id=(?P<id2>\w+))"
    __version__ = "0.3"
    __description__ = """NetFolder Crypter Plugin"""
    __author_name__ = ("RaNaN", "fragonib")
    __author_mail__ = ("RaNaN@pyload.org", "fragonib[AT]yahoo[DOT]es")

    def decrypt(self, pyfile):
        
        # Request package
        self.html = self.load(pyfile.url)
        
        # Check for password protection    
        if self.isPasswordProtected():
            self.html = self.submitPassword()
            if self.html is None:
                self.fail("Incorrect password, please set right password on Add package form and retry")

        # Get package name and folder
        (package_name, folder_name) = self.getPackageNameAndFolder()

        # Get package links
        package_links = self.getLinks()

        # Set package
        self.packages = [(package_name, package_links, folder_name)]
        
        
    def isPasswordProtected(self):
        
        if '<input type="password" name="password"' in self.html:
            self.logDebug("Links are password protected")
            return True
        return False


    def submitPassword(self):
        # Gather data
        try:
            m = re.match(self.__pattern__, self.pyfile.url)
            id = max(m.group('id1'), m.group('id2')) 
        except AttributeError:
            self.logDebug("Unable to get package id from url [%s]" % url)
            return
        url = "http://netfolder.in/folder.php?folder_id=" + id
        password = self.getPassword()
                   
        # Submit package password     
        post = { 'password' : password, 'save' : 'Absenden' }
        self.logDebug("Submitting password [%s] for protected links with id [%s]" % (password, id))
        html = self.load(url, {}, post)
        
        # Check for invalid password
        if '<div class="InPage_Error">' in html:
            self.logDebug("Incorrect password, please set right password on Edit package form and retry")
            return None
        
        return html 
    
    
    def getPackageNameAndFolder(self):
        title_re = r'<div class="Text">Inhalt des Ordners <span(.*)>(?P<title>.+)</span></div>'
        m = re.search(title_re, self.html)
        if m is not None:
            name = folder = m.group('title')
            self.logDebug("Found name [%s] and folder [%s] in package info" % (name, folder))
            return name, folder
        else:
            name = self.pyfile.package().name
            folder = self.pyfile.package().folder
            self.logDebug("Package info not found, defaulting to pyfile name [%s] and folder [%s]" % (name, folder))
            return name, folder
        
        
    def getLinks(self):
        links = re.search(r'name="list" value="(.*?)"', self.html).group(1).split(",")
        self.logDebug("Package has %d links" % len(links))
        return links
