#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

from module.plugins.Hoster import Hoster

class DlFreeFr(Hoster):
    __name__ = "DlFreeFr"
    __type__ = "hoster"
    __pattern__ = r"http://dl\.free\.fr/([a-zA-Z0-9]+|getfile\.pl\?file=/[a-zA-Z0-9]+)$"
    __version__ = "0.1"
    __description__ = """dl.free.fr download hoster"""
    __author_name__ = ("the-razer")
    __author_mail__ = ("daniel_ AT gmx DOT net")

    def setup(self):
        self.html = None
        self.multiDL = False

    def process(self, pyfile):

        self.download_html()

        if not self.file_exists():
            self.log.debug(self.__name__+": File not yet available.")
            self.offline()
        
        pyfile.name = self.get_file_name()
        
        url = self.get_file_url()
        if url:
            self.download(url)
        else:
            self.offline()

    def download_html(self):
        self.html = self.load(self.pyfile.url, cookies=False)
        
    def file_exists(self):
        warnings = (r"Erreur 404 - Document non trouv",
                    r"Fichier inexistant.",
                    r"Le fichier demand&eacute; n'a pas &eacute;t&eacute; trouv&eacute;")
        expr = '(' + '|'.join(warnings) + ')'
        if re.search(expr, self.html) is not None:
            return False 
        return True
        
    def get_file_url(self):
        self.log.debug(self.__name__+": Getting file URL")
        file_url_pattern = r'href="(?P<url>http://.*?)">T&eacute;l&eacute;charger ce fichier'
        
        m = re.search(file_url_pattern, self.html)
        if m is not None:
            url = m.group('url')
            self.log.debug(self.__name__+": File URL [%s]" % url)
            return url
        else:
            self.log.debug(self.__name__+": Error getting URL")
            return False

    def get_file_name(self):
        self.log.debug(self.__name__+": Getting file name")
        
        file_name_pattern = r"Fichier:</td>\s*<td.*>(?P<name>.*?)</td>"
        m = re.search(file_name_pattern, self.html)
        
        if m is not None:
            name = m.group('name').strip()
            self.log.debug(self.__name__+": File name [%s]" % name)
            return name
        else:
            self.log.debug(self.__name__+": Could not find filename")
