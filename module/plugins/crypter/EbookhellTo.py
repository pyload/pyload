# -*- coding: utf-8 -*-

import re

from ..internal.Crypter import Crypter


class EbookhellTo(Crypter):
    __name__ = "EbookhellTo"
    __type__ = "crypter"
    __version__ = "0.01"
    __status__ = "testing"

    __pattern__ = r'https://ebook-hell\.to/category/(?P<cat>.+)/(?P<ID>.+)-(\d+)\.html'
    __config__ = [("activated", "bool", "Activated", True),
                  ("folder_per_package", "Default;Yes;No", "Create folder for each package", "Default")]

    __description__ = """Ebook-hell.to decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Ozzieisaacs", "")]

    #: Constants
    PATTERN_SUPPORTED_CRYPT = r'<A HREF="(?P<LINK>.*)" TARGET="_blank"><IMG src="/gfx/download/download_button.png"'

    PATTERN_TITLE = r'<TITLE> (?P<TITLE>.*) Gratis Deutsche eBooks downloaden</TITLE>'
    PATTERN_PASSWORD = r'<B>Passwort:</B><font color="#ff0000"> (?P<PWD>.*?)</font>'
    # PATTERN_DL_LINK_PAGE = r'"(dl_links_\d+_\d+\.html)"'
    # PATTERN_REDIRECT_LINKS = r'disabled\'" href="(.*)" id'
    LIST_PWDIGNORE = ["kein Eintrag", "-"]

    def decrypt(self, pyfile):
        #: Init
        self.pyfile = pyfile
        self.package = pyfile.package()

        #: Decrypt and add links
        pack_name, self.urls, folder_name, pack_pwd = self.decrypt_links(
            self.pyfile.url)
        if pack_pwd:
            self.pyfile.package().password = pack_pwd
        self.packages = [(pack_name, self.urls, folder_name)]

    def decrypt_links(self, url):
        linklist = []
        name = self.package.name
        folder = self.package.folder
        password = None
        html = self.load(url)
        id = re.findall(self.PATTERN_SUPPORTED_CRYPT, html, re.I) #.group('LINK')
        #: Webpage title / Package name
        titledata = re.search(self.PATTERN_TITLE, html, re.I)
        if not titledata:
            self.log_warning("No title data found, has site changed?")
        else:
            title = titledata.group('TITLE').strip()
            if title:
                name = folder = title
                self.log_debug(
                    "Package info found, name [%s] and folder [%s]" %
                    (name, folder))
        #: Password
        pwddata = re.search(self.PATTERN_PASSWORD, html, re.I | re.S)
        if not pwddata:
            self.log_warning("No password data found, has site changed?")
        else:
            pwd = pwddata.group('PWD').strip()
            if pwd and not (pwd in self.LIST_PWDIGNORE):
                password = pwd
                self.log_debug(
                    "Package info found, password [%s]" %
                    password)

        #: Process links (dl_link)
        for link in id:
            linklist.append(link)

        #: Log result
        if not linklist:
            self.fail(_("Unable to extract links (maybe plugin out of date?)"))
        else:
            for i, link in enumerate(linklist):
                self.log_debug(
                    "Supported link %d/%d: %s" %
                    (i + 1, len(linklist), link))

        #: All done, return to caller
        return name, linklist, folder, password
