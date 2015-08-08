# -*- coding: utf-8 -*-

import re

from module.plugins.internal.Crypter import Crypter


class SexuriaCom(Crypter):
    __name__    = "SexuriaCom"
    __type__    = "crypter"
    __version__ = "0.04"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?sexuria\.com/(v1/)?(Pornos_Kostenlos_.+?_(\d+)\.html|dl_links_\d+_\d+\.html|id=\d+\&part=\d+\&link=\d+)'
    __config__  = [("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description__ = """Sexuria.com decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("NETHead", "NETHead.AT.gmx.DOT.net")]


    PATTERN_SUPPORTED_MAIN     = r'http://(www\.)?sexuria\.com/(v1/)?Pornos_Kostenlos_.+?_(\d+)\.html'
    PATTERN_SUPPORTED_CRYPT    = r'http://(www\.)?sexuria\.com/(v1/)?dl_links_\d+_(?P<ID>\d+)\.html'
    PATTERN_SUPPORTED_REDIRECT = r'http://(www\.)?sexuria\.com/out\.php\?id=(?P<ID>\d+)\&part=\d+\&link=\d+'
    PATTERN_TITLE              = r'<title> - (?P<TITLE>.*) Sexuria - Kostenlose Pornos - Rapidshare XXX Porn</title>'
    PATTERN_PASSWORD           = r'<strong>Passwort: </strong></div></td>.*?bgcolor="#EFEFEF">(?P<PWD>.*?)</td>'
    PATTERN_DL_LINK_PAGE       = r'"(dl_links_\d+_\d+\.html)"'
    PATTERN_REDIRECT_LINKS     = r'value="(http://sexuria\.com/out\.php\?id=\d+\&part=\d+\&link=\d+)" readonly'


    def decrypt(self, pyfile):
        #: Init
        self.pyfile = pyfile
        self.package = pyfile.package()

        #: Get package links
        package_name, self.links, folder_name, package_pwd = self.decrypt_links(self.pyfile.url)
        self.packages = [(package_name, self.links, folder_name)]


    def decrypt_links(self, url):
        linklist = []
        name     = self.package.name
        folder   = self.package.folder
        password = None

        if re.match(self.PATTERN_SUPPORTED_MAIN, url, re.I):
            #: Processing main page
            html = self.load(url)
            links = re.findall(self.PATTERN_DL_LINK_PAGE, html, re.I)
            for link in links:
                linklist.append("http://sexuria.com/v1/" + link)

        elif re.match(self.PATTERN_SUPPORTED_REDIRECT, url, re.I):
            #: Processing direct redirect link (out.php), redirecting to main page
            id = re.search(self.PATTERN_SUPPORTED_REDIRECT, url, re.I).group('ID')
            if id:
                linklist.append("http://sexuria.com/v1/Pornos_Kostenlos_liebe_%s.html" % id)

        elif re.match(self.PATTERN_SUPPORTED_CRYPT, url, re.I):
            #: Extract info from main file
            id = re.search(self.PATTERN_SUPPORTED_CRYPT, url, re.I).group('ID')
            html = self.load("http://sexuria.com/v1/Pornos_Kostenlos_info_%s.html" % id)

            title = re.search(self.PATTERN_TITLE, html, re.I).group('TITLE').strip()
            if title:
                name = folder = title
                self.log_debug("Package info found, name [%s] and folder [%s]" % (name, folder))

            pwd = re.search(self.PATTERN_PASSWORD, html, re.I | re.S).group('PWD')
            if pwd and pwd not in ("Kein Passwort", "-"):
                password = pwd.strip()
                self.log_debug("Password info [%s] found" % password)

            #: Process link (dl_link)
            html = self.load(url)
            links = re.findall(self.PATTERN_REDIRECT_LINKS, html, re.I)
            if len(links) == 0:
                self.log_error(_("Broken for link: %s") % link)
            else:
                for link in links:
                    link = link.replace("http://sexuria.com/", "http://www.sexuria.com/")
                    finallink = self.load(link, just_header=True)['location']
                    if not finallink or "sexuria.com/" in finallink:
                        self.log_error(_("Broken for link: %s") % link)
                    else:
                        linklist.append(finallink)

        #: Debug log
        self.log_debug("%d supported links" % len(linklist))
        for i, link in enumerate(linklist):
            self.log_debug("Supported link %d, %s" % (i + 1, link))

        return name, linklist, folder, password
