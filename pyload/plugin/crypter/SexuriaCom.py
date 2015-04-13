# -*- coding: utf-8 -*-

import re

from pyload.plugin.Crypter import Crypter


class SexuriaCom(Crypter):
    __name    = "SexuriaCom"
    __type    = "crypter"
    __version = "0.01"

    __pattern = r'http://(?:www\.)?sexuria\.com/(v1/)?(Pornos_Kostenlos_.+?_(\d+)\.html|dl_links_\d+_\d+\.html|id=\d+\&part=\d+\&link=\d+)'
    __config  = [("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description = """Sexuria.com decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("NETHead", "NETHead.AT.gmx.DOT.net")]


    PATTERN_SUPPORTED_MAIN     = re.compile(r'http://(www\.)?sexuria\.com/(v1/)?Pornos_Kostenlos_.+?_(\d+)\.html', re.I)
    PATTERN_SUPPORTED_CRYPT    = re.compile(r'http://(www\.)?sexuria\.com/(v1/)?dl_links_\d+_(?P<ID>\d+)\.html', re.I)
    PATTERN_SUPPORTED_REDIRECT = re.compile(r'http://(www\.)?sexuria\.com/out\.php\?id=(?P<ID>\d+)\&part=\d+\&link=\d+', re.I)
    PATTERN_TITLE              = re.compile(r'<title> - (?P<TITLE>.*) Sexuria - Kostenlose Pornos - Rapidshare XXX Porn</title>', re.I)
    PATTERN_PASSWORD           = re.compile(r'<strong>Passwort: </strong></div></td>.*?bgcolor="#EFEFEF">(?P<PWD>.*?)</td>', re.I | re.S)
    PATTERN_DL_LINK_PAGE       = re.compile(r'"(dl_links_\d+_\d+\.html)"', re.I)
    PATTERN_REDIRECT_LINKS     = re.compile(r'value="(http://sexuria\.com/out\.php\?id=\d+\&part=\d+\&link=\d+)" readonly', re.I)


    def decrypt(self, pyfile):
        # Init
        self.pyfile = pyfile
        self.package = pyfile.package()

        # Get package links
        package_name, self.links, folder_name, package_pwd = self.decryptLinks(self.pyfile.url)
        self.packages = [(package_name, self.links, folder_name)]


    def decryptLinks(self, url):
        linklist = []
        name = self.package.name
        folder = self.package.folder
        password = None

        if re.match(self.PATTERN_SUPPORTED_MAIN, url):
            # Processing main page
            html = self.load(url)
            links = re.findall(self.PATTERN_DL_LINK_PAGE, html)
            for link in links:
                linklist.append("http://sexuria.com/v1/" + link)

        elif re.match(self.PATTERN_SUPPORTED_REDIRECT, url):
            # Processing direct redirect link (out.php), redirecting to main page
            id = re.search(self.PATTERN_SUPPORTED_REDIRECT, url).group('ID')
            if id:
                linklist.append("http://sexuria.com/v1/Pornos_Kostenlos_liebe_%s.html" % id)

        elif re.match(self.PATTERN_SUPPORTED_CRYPT, url):
            # Extract info from main file
            id = re.search(self.PATTERN_SUPPORTED_CRYPT, url).group('ID')
            html = self.load("http://sexuria.com/v1/Pornos_Kostenlos_info_%s.html" % id, decode=True)

            title = re.search(self.PATTERN_TITLE, html).group('TITLE').strip()
            if title:
                name = folder = title
                self.logDebug("Package info found, name [%s] and folder [%s]" % (name, folder))

            pwd = re.search(self.PATTERN_PASSWORD, html).group('PWD')
            if pwd:
                password = pwd.strip()
                self.logDebug("Password info [%s] found" % password)

            # Process link (dl_link)
            html = self.load(url)
            links = re.findall(self.PATTERN_REDIRECT_LINKS, html)
            if len(links) == 0:
                self.LogError("Broken for link %s" % link)
            else:
                for link in links:
                    link = link.replace("http://sexuria.com/", "http://www.sexuria.com/")
                    finallink = self.load(link, just_header=True)['location']
                    if not finallink or "sexuria.com/" in finallink:
                        self.LogError("Broken for link %s" % link)
                    else:
                        linklist.append(finallink)

        # Debug log
        self.logDebug("%d supported links" % len(linklist))
        for i, link in enumerate(linklist):
            self.logDebug("Supported link %d, %s" % (i + 1, link))

        return name, linklist, folder, password
