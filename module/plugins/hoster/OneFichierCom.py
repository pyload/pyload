#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

from module.plugins.Hoster import Hoster

class OneFichierCom(Hoster):
    __name__ = "OneFichierCom"
    __type__ = "hoster"
    __pattern__ = r"http://[a-z0-9]+\.1fichier\.com/(.*)"
    __version__ = "0.1"
    __description__ = """1fichier.com download hoster"""
    __author_name__ = ("fragonib")
    __author_mail__ = ("fragonib AT yahoo DOT es")

    def setup(self):
        self.html = None
        self.multiDL = False

    def process(self, pyfile):

        self.download_html()

        if not self.file_exists():
            self.log.debug("OneFichierCom: File not yet available.")
            self.offline()
        
        pyfile.name = self.get_file_name()
        pyfile.size = self.get_file_size()
        
        url = self.get_file_url()
        self.download(url)

    def download_html(self):
        self.html = self.load(self.pyfile.url, cookies=False)
        
    def file_exists(self):
        warnings = (r"The requested file could not be found",
                    r"The file may has been deleted by its owner",
                    r"Le fichier demandé n'existe pas\.",
                    r"Il a pu être supprimé par son propriétaire\.")
        expr = '(' + '|'.join(warnings) + ')'
        
        if re.search(expr, self.html) is not None:
            return False 
        return True
        
    def get_file_url(self):
        self.log.debug("OneFichierCom: Getting file URL")
        file_url_pattern = r"<br/>\&nbsp;<br/>\&nbsp;<br/>\&nbsp;[\t\n\r ]+<a href=\"(http://.*?)\""
        
        m = re.search(file_url_pattern, self.html)
        if m is not None:
            url = m.group(1)
            self.log.debug("OneFichierCom: File URL [%s]" % url)
            return url

    def get_file_name(self):
        self.log.debug("OneFichierCom: Getting file name")
        file_name_patterns = (
            r"content=\"Téléchargement du fichier (.*?)\">", 
            r"(>Cliquez ici pour télécharger|>Click here to download) (.*?)</a>",
            r"\">(Nom du fichier :|File name :)</th>[\t\r\n ]+<td>(.*?)</td>",
            r"<title>Download of (.*?)</title>"
        )
    
        for pattern in file_name_patterns:
            m = re.search(pattern, self.html)
            if m is not None:
                name = m.group(1).strip()
                self.log.debug("OneFichierCom: File name [%s]" % name)
                return name
            
    def get_file_size(self):
        self.log.debug("OneFichierCom: Getting file size")
        file_size_pattern = r"<th>(Taille :|File size :)</th>[\t\n\r ]+<td>(\d*)\s+(.*?)</td>"
        
        m = re.search(file_size_pattern, self.html)
        if m is not None:
            size = m.group(2)
            units = m.group(3)
            multiplier = 1
            if units in ("Go", "Gb"):
                multiplier = 1024 ** 3
            if units in ("Mo", "Mb"):
                multiplier = 1024 ** 2
            if units in ("Ko", "Kb"):
                multiplier = 1024 ** 1
            bytes = int(size) * multiplier
            self.log.debug("OneFichierCom: File size [%s] bytes" % bytes)
            return bytes
                    