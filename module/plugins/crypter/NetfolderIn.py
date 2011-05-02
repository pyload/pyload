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
            self.log.debug("%s: Links are password protected" % self.__name__)
            return True
        return False


    def submitPassword(self):
        # Gather data
        try:
            m = re.match(self.__pattern__, self.pyfile.url)
            id = max(m.group('id1'), m.group('id2')) 
        except AttributeError:
            self.log.debug("%s: Unable to get package id from url [%s]" % (self.__name__, url))
            return
        url = "http://netfolder.in/folder.php?folder_id=" + id
        password = self.pyfile.package().password
                   
        # Submit package password     
        post = { 'password' : password, 'save' : 'Absenden' }
        self.log.debug("%s: Submitting password [%s] for protected links with id [%s]" % (self.__name__, password, id))
        html = self.load(url, {}, post)
        
        # Check for invalid password
        if '<div class="InPage_Error">' in html:
            self.log.debug("%s: Incorrect password, please set right password on Edit package form and retry" % self.__name__)
            return None
        
        return html 
    
    
    def getPackageNameAndFolder(self):
        title_re = r'<div class="Text">Inhalt des Ordners <span(.*)>(?P<title>.+)</span></div>'
        m = re.search(title_re, self.html)
        if m is not None:
            name = folder = m.group('title')
            self.log.debug("%s: Found name [%s] and folder [%s] in package info" % (self.__name__, name, folder))
            return (name, folder)
        else:
            name = self.pyfile.package().name
            folder = self.pyfile.package().folder
            self.log.debug("%s: Package info not found, defaulting to pyfile name [%s] and folder [%s]" % (self.__name__, name, folder))
            return (name, folder)
        
        
    def getLinks(self):
        links = re.search(r'name="list" value="(.*?)"', self.html).group(1).split(",")
        self.log.debug("%s: Package has %d links" % (self.__name__, len(links)))
        return links
