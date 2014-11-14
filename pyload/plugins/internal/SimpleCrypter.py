# -*- coding: utf-8 -*-

import re

from urlparse import urlparse

from pyload.plugins.Crypter import Crypter
from module.plugins.Plugin import Fail
from module.plugins.internal.SimpleHoster import _error, _wait, parseFileInfo, replace_patterns, set_cookies
from pyload.utils import fixup, html_unescape


class SimpleCrypter(Crypter):
    __name__    = "SimpleCrypter"
    __type__    = "crypter"
    __version__ = "0.29"

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

      LINK_PATTERN: group(1) must be a download link or a regex to catch more links
        example: LINK_PATTERN = r'<div class="link"><a href="(.+?)"'

      NAME_PATTERN: (optional) folder name or webpage title
        example: NAME_PATTERN = r'<title>Files of: (?P<N>[^<]+) folder</title>'

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

    NAME_REPLACEMENTS = [("&#?\w+;", fixup)]
    URL_REPLACEMENTS  = []

    TEXT_ENCODING = False  #: Set to True or encoding name if encoding in http header is not correct
    COOKIES       = True  #: or False or list of tuples [(domain, name, value)]

    LOGIN_ACCOUNT = False
    LOGIN_PREMIUM = False


    #@TODO: remove in 0.4.10
    def init(self):
        self.info = {}

        account_name = (self.__name__ + ".py").replace("Folder.py", "").replace(".py", "")
        account = self.core.accountManager.getAccountPlugin(account_name)

        if account and account.canUse():
            self.user, data = account.selectAccount()
            self.req = account.getAccountRequest(self.user)
            self.premium = account.isPremium(self.user)

            self.account = account


    def prepare(self):
        if self.LOGIN_ACCOUNT and not self.account:
            self.fail(_("Required account not found"))

        if self.LOGIN_PREMIUM and not self.premium:
            self.fail(_("Required premium account not found"))

        if isinstance(self.COOKIES, list):
            set_cookies(self.req.cj, self.COOKIES)

        self.pyfile.url = replace_patterns(self.pyfile.url, self.URL_REPLACEMENTS)

        self.html = self.load(self.pyfile.url, decode=not self.TEXT_ENCODING, cookies=bool(self.COOKIES))

        if isinstance(self.TEXT_ENCODING, basestring):
            self.html = unicode(self.html, self.TEXT_ENCODING)


    def decrypt(self, pyfile):
        self.prepare()

        if self.html is None:
            self.fail(_("No html retrieved"))

        if not self.info:
            self.getFileInfo()

        self.links = self.getLinks()

        if hasattr(self, 'PAGES_PATTERN') and hasattr(self, 'loadPage'):
            self.handleMultiPages()

        self.logDebug("Package has %d links" % len(self.links))

        if self.links:
            self.packages = [(self.info['name'], self.links, self.info['folder'])]


    def getFileInfo(self):
        name, size, status, url = parseFileInfo(self)

        if name and name != url:
            self.pyfile.name = name
        else:
            self.pyfile.name = self.info['name'] = urlparse(html_unescape(name)).path.split("/")[-1]

        if status is 1:
            self.offline()

        elif status is 6:
            self.tempOffline()

        self.info['folder'] = self.pyfile.name

        self.logDebug("FILE NAME: %s" % self.pyfile.name)
        return self.info


    def getLinks(self):
        """
        Returns the links extracted from self.html
        You should override this only if it's impossible to extract links using only the LINK_PATTERN.
        """
        return re.findall(self.LINK_PATTERN, self.html)


    def handleMultiPages(self):
        try:
            m = re.search(self.PAGES_PATTERN, self.html)
            pages = int(m.group(1))
        except:
            pages = 1

        for p in xrange(2, pages + 1):
            self.html = self.loadPage(p)
            self.links += self.getLinks()


    #@TODO: Remove in 0.4.10
    def wait(self, seconds=0, reconnect=None):
        return _wait(self, seconds, reconnect)


    def error(self, reason="", type="parse"):
        return _error(self, reason, type)
