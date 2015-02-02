# -*- coding: utf-8 -*-

import re

from urlparse import urljoin, urlparse

from module.plugins.Crypter import Crypter
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo, replace_patterns, set_cookies
from module.utils import fixup


class SimpleCrypter(Crypter, SimpleHoster):
    __name__    = "SimpleCrypter"
    __type__    = "crypter"
    __version__ = "0.43"

    __pattern__ = r'^unmatchable$'
    __config__  = [("use_subfolder", "bool", "Save package to subfolder", True),  #: Overrides core.config['general']['folder_per_package']
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description__ = """Simple decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it"),
                       ("zoidberg", "zoidberg@mujmail.cz"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    """
    Following patterns should be defined by each crypter:

      LINK_PATTERN: Download link or regex to catch links in group(1)
        example: LINK_PATTERN = r'<div class="link"><a href="(.+?)"'

      NAME_PATTERN: (optional) folder name or page title
        example: NAME_PATTERN = r'<title>Files of: (?P<N>[^<]+) folder</title>'

      OFFLINE_PATTERN: (optional) Checks if the page is unreachable
        example: OFFLINE_PATTERN = r'File (deleted|not found)'

      TEMP_OFFLINE_PATTERN: (optional) Checks if the page is temporarily unreachable
        example: TEMP_OFFLINE_PATTERN = r'Server maintainance'


    You can override the getLinks method if you need a more sophisticated way to extract the links.


    If the links are splitted on multiple pages you can define the PAGES_PATTERN regex:

      PAGES_PATTERN: (optional) group(1) should be the number of overall pages containing the links
        example: PAGES_PATTERN = r'Pages: (\d+)'

    and its loadPage method:


      def loadPage(self, page_n):
          return the html of the page number page_n
    """

    LINK_PATTERN = None

    NAME_REPLACEMENTS = [("&#?\w+;", fixup)]
    URL_REPLACEMENTS  = []

    TEXT_ENCODING = False  #: Set to True or encoding name if encoding in http header is not correct
    COOKIES       = True  #: or False or list of tuples [(domain, name, value)]

    LOGIN_ACCOUNT = False
    LOGIN_PREMIUM = False


    #@TODO: Remove in 0.4.10
    def init(self):
        account_name = (self.__name__ + ".py").replace("Folder.py", "").replace(".py", "")
        account      = self.pyfile.m.core.accountManager.getAccountPlugin(account_name)

        if account and account.canUse():
            self.user, data = account.selectAccount()
            self.req        = account.getAccountRequest(self.user)
            self.premium    = account.isPremium(self.user)

            self.account = account


    def prepare(self):
        self.pyfile.error = ""  #@TODO: Remove in 0.4.10

        self.info  = {}
        self.html  = ""
        self.links = []  #@TODO: Move to hoster class in 0.4.10

        if self.LOGIN_PREMIUM and not self.premium:
            self.fail(_("Required premium account not found"))

        if self.LOGIN_ACCOUNT and not self.account:
            self.fail(_("Required account not found"))

        self.req.setOption("timeout", 120)

        if isinstance(self.COOKIES, list):
            set_cookies(self.req.cj, self.COOKIES)

        self.pyfile.url = replace_patterns(self.pyfile.url, self.URL_REPLACEMENTS)


    def decrypt(self, pyfile):
        self.prepare()

        self.preload()
        self.checkInfo()

        self.links = self.getLinks()

        if hasattr(self, 'PAGES_PATTERN') and hasattr(self, 'loadPage'):
            self.handlePages(pyfile)

        self.logDebug("Package has %d links" % len(self.links))

        if self.links:
            self.packages = [(self.info['name'], self.links, self.info['folder'])]

        elif not self.urls and not self.packages:  #@TODO: Remove in 0.4.10
            self.fail(_("No link grabbed"))


    def checkNameSize(self, getinfo=True):
        if not self.info or getinfo:
            self.logDebug("File info (BEFORE): %s" % self.info)
            self.info.update(self.getInfo(self.pyfile.url, self.html))
            self.logDebug("File info (AFTER): %s"  % self.info)

        try:
            url  = self.info['url'].strip()
            name = self.info['name'].strip()
            if name and name != url:
                self.pyfile.name = name

        except Exception:
            pass

        try:
            folder = self.info['folder'] = self.pyfile.name

        except Exception:
            pass

        self.logDebug("File name: %s"   % self.pyfile.name,
                      "File folder: %s" % self.pyfile.name)


    def getLinks(self):
        """
        Returns the links extracted from self.html
        You should override this only if it's impossible to extract links using only the LINK_PATTERN.
        """
        url_p   = urlparse(self.pyfile.url)
        baseurl = "%s://%s" % (url_p.scheme, url_p.netloc)

        return [urljoin(baseurl, link) if not urlparse(link).scheme else link \
                for link in re.findall(self.LINK_PATTERN, self.html)]


    def handlePages(self, pyfile):
        try:
            pages = int(re.search(self.PAGES_PATTERN, self.html).group(1))
        except Exception:
            pages = 1

        for p in xrange(2, pages + 1):
            self.html = self.loadPage(p)
            self.links += self.getLinks()
