#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

from module.plugins.Hoster import Hoster

class OneFichierCom(Hoster):
    __name__ = "OneFichierCom"
    __type__ = "hoster"
    __pattern__ = r"http://[a-z0-9]+\.1fichier\.com/(.*)"
    __version__ = "0.2"
    __description__ = """1fichier.com download hoster"""
    __author_name__ = ("fragonib")
    __author_mail__ = ("fragonib[AT]yahoo[DOT]es")

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
        pattern = '(' + '|'.join(warnings) + ')'
        if re.search(pattern, self.html) is not None:
            return False 
        return True
        
    def get_file_url(self):
        file_url_pattern = r"<br/>\&nbsp;<br/>\&nbsp;<br/>\&nbsp;[\t\n\r ]+<a href=\"(?P<url>http://.*?)\""
        
        m = re.search(file_url_pattern, self.html)
        if m is not None:
            url = m.group('url')
            self.log.debug("OneFichierCom: Got file URL [%s]" % url)
            return url

    def get_file_name(self):
        file_name_patterns = (
            r"\">(Nom du fichier :|File name :)</th>[\t\r\n ]+<td>(?P<name>.*?)</td>",
            r"(>Cliquez ici pour télécharger|>Click here to download) (?P<name>.*?)</a>",
            r"content=\"(Téléchargement du fichier |Download the file named )(?P<name>.*?)\">", 
            r"<title>(Téléchargement du fichier|Download the file)\s*:\s*(?P<name>.*?)</title>"
        )
    
        for pattern in file_name_patterns:
            m = re.search(pattern, self.html)
            if m is not None:
                name = m.group('name').strip()
                self.log.debug("OneFichierCom: Got file name [%s]" % name)
                return name
            
    def get_file_size(self):
        file_size_pattern = r"<th>(Taille :|File size :)</th>[\t\n\r ]+<td>(?P<size>\d*)\s+(?P<units>.*?)</td>"        
        m = re.search(file_size_pattern, self.html)
        if m is not None:
            size = int(m.group('size'))
            units = m.group('units')[0].upper()
            try:
                multiplier = 1024 ** {"K":1, "M":2, "G":3}[units]
            except KeyError:
                multiplier = 1
            bytes = size * multiplier
            self.log.debug("OneFichierCom: Got file size of [%s] bytes" % bytes)
            return bytes