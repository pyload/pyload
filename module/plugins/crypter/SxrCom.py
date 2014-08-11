# -*- coding: utf-8 -*-

from module.plugins.Crypter import Crypter
import re

class SxrCom(Crypter):
    __name__ = "SxrCom"
    __type__ = "crypter"
    __pattern__ = r"http://(www\.)?sexuria\.com/(v1/)?Pornos_Kostenlos_.+?_(\d+)\.html|http://(www\.)?sexuria\.com/(v1/)?dl_links_\d+_\d+\.html|http://(www\.)?sexuria\.com/out\.php\?id=(\d+)\&part=\d+\&link=\d+"
    __version__ = "0.2"
    __description__ = """Sexuria.com Crypter Plugin"""
    __author_name__ = ("NETHead")
    __author_mail__ = ("NETHead[AT]gmx[DOT]net")

    # Constants
    PATTERN_SUPPORTED_MAIN     = re.compile(r'http://(www\.)?sexuria\.com/(v1/)?Pornos_Kostenlos_.+?_(\d+)\.html', flags=re.IGNORECASE)
    PATTERN_SUPPORTED_CRYPT    = re.compile(r'http://(www\.)?sexuria\.com/(v1/)?dl_links_\d+_(?P<id>\d+)\.html', flags=re.IGNORECASE)
    PATTERN_SUPPORTED_REDIRECT = re.compile(r'http://(www\.)?sexuria\.com/out\.php\?id=(?P<id>\d+)\&part=\d+\&link=\d+', flags=re.IGNORECASE)
    PATTERN_TITLE              = re.compile(r'<title> - (?P<title>.*) Sexuria - Kostenlose Pornos - Rapidshare XXX Porn</title>', flags=re.IGNORECASE)
    PATTERN_PASSWORD           = re.compile(r'<strong>Passwort: </strong></div></td>.*?bgcolor="#EFEFEF">(?P<pwd>.*?)</td>', flags=re.IGNORECASE | re.DOTALL)
    PATTERN_DL_LINK_PAGE       = re.compile(r'"(dl_links_\d+_\d+\.html)"', flags=re.IGNORECASE)
    PATTERN_REDIRECT_LINKS     = re.compile(r'value="(http://sexuria\.com/out\.php\?id=\d+\&part=\d+\&link=\d+)" readonly', flags=re.IGNORECASE)


    def setup(self):
        self.html = None


    def decrypt(self, pyfile):
        # Init
        self.pyfile = pyfile
        self.package = pyfile.package()

        # Get package links
        try:
            (package_name, package_links, folder_name, password) = self.getLinks(self.pyfile.url)
            self.packages = [(package_name, package_links, folder_name)]
            self.pyfile.package().password = password
        except:
            self.fail("Unable to decrypt package")


    def getLinks(self, url):
        # Initialize
        linklist = []
        name = self.package.name
        folder = self.package.folder
        password = None

        # Process url
        if re.match(self.PATTERN_SUPPORTED_MAIN, url):
            # Processing main page
            html = self.load(url)
            links = re.findall(self.PATTERN_DL_LINK_PAGE, html)
            for link in links:
                linklist.append("http://sexuria.com/v1/" + link)
        elif re.match(self.PATTERN_SUPPORTED_REDIRECT, url):
            # Processing direct redirect link (out.php)
            id = re.search(self.PATTERN_SUPPORTED_REDIRECT, url).group('id')
            if id:
                linklist.append("http://sexuria.com/v1/Pornos_Kostenlos_liebe_" + id + ".html")
        elif re.match(self.PATTERN_SUPPORTED_CRYPT, url):
            # Processing crypted link (dl_links)
            id = re.search(self.PATTERN_SUPPORTED_CRYPT, url).group('id')
            html = self.load("http://sexuria.com/v1/Pornos_Kostenlos_info_" + id + ".html")
            title = re.search(self.PATTERN_TITLE, html).group('title').strip()
            if title:
                name = folder = title
                self.logDebug("Package info found, name [%s] and folder [%s]" % (name, folder))
            pwd = re.search(self.PATTERN_PASSWORD, html).group('pwd')
            if pwd:
                password = pwd.strip()
                self.logDebug("Password info [%s] found" % password)
            html = self.load(url)
            links = re.findall(self.PATTERN_REDIRECT_LINKS, html)
            self.logDebug("Found %d redirect links " % len(links))
            if len(links) == 0:
                self.logDebug("Decrypter broken for link %s" % link)
            else:
                for link in links:
                    link = link.replace("http://sexuria.com/", "http://www.sexuria.com/")
                    finallink = self.load(link, just_header = True)['location']
                    if (finallink == None) or ("sexuria.com/" in finallink):
                        self.logDebug("Decrypter broken for link %s" % link)
                    else:
                        linklist.append(finallink)

        # Log and return
        self.logDebug("Result: %d supported links" % len(linklist))
        for i, link in enumerate(linklist):
            self.logDebug("Supported link %d, %s" % (i+1, link))

        return name, linklist, folder, password
