# -*- coding: utf-8 -*-

import re

from traceback import print_exc

from module.network.RequestFactory import getURL
from module.plugins.Crypter import Crypter
from module.plugins.Plugin import Fail
from module.plugins.internal.SimpleHoster import _error, replace_patterns, set_cookies
from module.utils import fixup, html_unescape


class SimpleCrypter(Crypter):
    __name__ = "SimpleCrypter"
    __type__ = "crypter"
    __version__ = "0.19"

    __pattern__ = None

    __description__ = """Simple decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("stickell", "l.stickell@yahoo.it"),
                   ("zoidberg", "zoidberg@mujmail.cz"),
                   ("Walter Purcaro", "vuolter@gmail.com")]


    """
    Following patterns should be defined by each crypter:

      LINK_PATTERN: group(1) must be a download link or a regex to catch more links
        example: LINK_PATTERN = r'<div class="link"><a href="(.+?)"'

      TITLE_PATTERN: (optional) group(1) should be the folder name or the webpage title
        example: TITLE_PATTERN = r'<title>Files of: ([^<]+) folder</title>'

      OFFLINE_PATTERN: (optional) Checks if the file is yet available online
        example: OFFLINE_PATTERN = r'File (deleted|not found)'

      TEMP_OFFLINE_PATTERN: (optional) Checks if the file is temporarily offline
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

    TITLE_REPLACEMENTS = [("&#?\w+;", fixup)]
    URL_REPLACEMENTS = []

    TEXT_ENCODING = False  #: Set to True or encoding name if encoding in http header is not correct
    COOKIES = True  #: or False or list of tuples [(domain, name, value)]

    LOGIN_ACCOUNT = False
    LOGIN_PREMIUM = False


    #@TODO: remove in 0.4.10
    def init(self):
        account_name = (self.__name__ + ".py").replace("Folder.py", "").replace(".py", "")
        account = self.core.accountManager.getAccountPlugin(account_name)

        if account and account.canUse():
            self.user, data = account.selectAccount()
            self.req = account.getAccountRequest(self.user)
            self.premium = account.isPremium(self.user)

            self.account = account


    def prepare(self):
        if self.LOGIN_ACCOUNT and not self.account:
            self.fail(_("Required account not found!"))

        if self.LOGIN_PREMIUM and not self.premium:
            self.fail(_("Required premium account not found!"))

        if isinstance(self.COOKIES, list):
            set_cookies(self.req.cj, self.COOKIES)

        url = self.pyfile.url = replace_patterns(self.pyfile.url, self.URL_REPLACEMENTS)
        self.html = getURL(url, decode=not self.TEXT_ENCODING, cookies=bool(self.COOKIES))


    def decrypt(self, pyfile):
        self.prepare()

        self.checkOnline()

        package_name, folder_name = self.getPackageNameAndFolder()

        self.package_links = self.getLinks()

        if hasattr(self, 'PAGES_PATTERN') and hasattr(self, 'loadPage'):
            self.handleMultiPages()

        self.logDebug("Package has %d links" % len(self.package_links))

        if self.package_links:
            self.packages = [(package_name, self.package_links, folder_name)]
        else:
            self.fail(_("Could not extract any links"))


    def getLinks(self):
        """
        Returns the links extracted from self.html
        You should override this only if it's impossible to extract links using only the LINK_PATTERN.
        """
        return re.findall(self.LINK_PATTERN, self.html)


    def checkOnline(self):
        if hasattr(self, "OFFLINE_PATTERN") and re.search(self.OFFLINE_PATTERN, self.html):
            self.offline()
        elif hasattr(self, "TEMP_OFFLINE_PATTERN") and re.search(self.TEMP_OFFLINE_PATTERN, self.html):
            self.tempOffline()


    def getPackageNameAndFolder(self):
        if isinstance(self.TEXT_ENCODING, basestring):
            self.html = unicode(self.html, self.TEXT_ENCODING)

        if hasattr(self, 'TITLE_PATTERN'):
            try:
                m = re.search(self.TITLE_PATTERN, self.html)
                name = replace_patterns(m.group(1).strip(), self.TITLE_REPLACEMENTS)
                folder = html_unescape(name)
            except:
                pass
            else:
                self.logDebug("Found name [%s] and folder [%s] in package info" % (name, folder))
                return name, folder

        name = self.pyfile.package().name
        folder = self.pyfile.package().folder
        self.logDebug("Package info not found, defaulting to pyfile name [%s] and folder [%s]" % (name, folder))

        return name, folder


    def handleMultiPages(self):
        try:
            m = re.search(self.PAGES_PATTERN, self.html)
            pages = int(m.group(1))
        except:
            pages = 1

        for p in xrange(2, pages + 1):
            self.html = self.loadPage(p)
            self.package_links += self.getLinks()


    def error(self, reason="", type="parse"):
        return _error(reason, type)
