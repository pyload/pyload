# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleCrypter import SimpleCrypter


class NetfolderIn(SimpleCrypter):
    __name__    = "NetfolderIn"
    __type__    = "crypter"
    __version__ = "0.72"

    __pattern__ = r'http://(?:www\.)?netfolder\.in/((?P<id1>\w+)/\w+|folder\.php\?folder_id=(?P<id2>\w+))'
    __config__  = [("use_subfolder", "bool", "Save package to subfolder", True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description__ = """NetFolder.in decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN", "RaNaN@pyload.org"),
                       ("fragonib", "fragonib[AT]yahoo[DOT]es")]


    NAME_PATTERN = r'<div class="Text">Inhalt des Ordners <span.*>(?P<N>.+)</span></div>'


    def prepare(self):
        super(NetfolderIn, self).prepare()

        # Check for password protection
        if self.isPasswordProtected():
            self.html = self.submitPassword()
            if not self.html:
                self.fail(_("Incorrect password, please set right password on Add package form and retry"))


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
            self.logDebug("Unable to get package id from url [%s]" % self.pyfile.url)
            return
        url = "http://netfolder.in/folder.php?folder_id=" + id
        password = self.getPassword()

        # Submit package password
        post = {'password': password, 'save': 'Absenden'}
        self.logDebug("Submitting password [%s] for protected links with id [%s]" % (password, id))
        html = self.load(url, {}, post)

        # Check for invalid password
        if '<div class="InPage_Error">' in html:
            self.logDebug("Incorrect password, please set right password on Edit package form and retry")
            return None

        return html


    def getLinks(self):
        links = re.search(r'name="list" value="(.*?)"', self.html).group(1).split(",")
        self.logDebug("Package has %d links" % len(links))
        return links
