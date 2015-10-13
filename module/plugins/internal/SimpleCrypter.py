# -*- coding: utf-8 -*-

import re

from module.plugins.internal.Crypter import Crypter
from module.plugins.internal.Plugin import replace_patterns, set_cookie, set_cookies
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class SimpleCrypter(Crypter, SimpleHoster):
    __name__    = "SimpleCrypter"
    __type__    = "crypter"
    __version__ = "0.67"
    __status__  = "testing"

    __pattern__ = r'^unmatchable$'
    __config__  = [("use_premium"          , "bool", "Use premium account if available"   , True),
                   ("use_subfolder"        , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description__ = """Simple decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]

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

      def load_page(self, page_n):
          return the html of the page number page_n
    """

    NAME_REPLACEMENTS    = []
    URL_REPLACEMENTS     = []

    COOKIES              = True   #: or False or list of tuples [(domain, name, value)]
    DIRECT_LINK          = True   #: Set to True to looking for direct link (as defined in handle_direct method), set to None to do it if self.account is True else False
    LOGIN_ACCOUNT        = False  #: Set to True to require account login
    LOGIN_PREMIUM        = False  #: Set to True to require premium account login
    # LEECH_HOSTER         = False  #: Set to True to leech other hoster link (as defined in handle_multi method)
    TEXT_ENCODING        = True   #: Set to encoding name if encoding value in http header is not correct
    PAGES_PATTERN        = None

    LINK_PATTERN         = None

    NAME_PATTERN         = None
    HASHSUM_PATTERN      = None
    OFFLINE_PATTERN      = None
    TEMP_OFFLINE_PATTERN = None

    WAIT_PATTERN         = None
    PREMIUM_ONLY_PATTERN = None
    HAPPY_HOUR_PATTERN   = None
    IP_BLOCKED_PATTERN   = None
    DL_LIMIT_PATTERN     = None
    SIZE_LIMIT_PATTERN   = None
    ERROR_PATTERN        = None


    #@TODO: Remove in 0.4.10
    def _setup(self):
        orig_name = self.__name__
        self.__name__ = re.sub(r'Folder$', "", self.__name__)
        super(SimpleCrypter, self)._setup()
        self.__name__ = orig_name


    #@TODO: Remove in 0.4.10
    def load_account(self):
        orig_name = self.__name__
        self.__name__ = re.sub(r'Folder$', "", self.__name__)
        super(SimpleCrypter, self).load_account()
        self.__name__ = orig_name


    def handle_direct(self, pyfile):
        for i in xrange(self.get_config("maxredirs", plugin="UserAgentSwitcher")):
            redirect = self.link or pyfile.url
            self.log_debug("Redirect #%d to: %s" % (i, redirect))

            header = self.load(redirect, just_header=True)
            if header.get('location'):
                self.link = header.get('location')
            else:
                break
        else:
            self.log_error(_("Too many redirects"))


    def prepare(self):
        self.links = []
        return super(SimpleCrypter, self).prepare()


    def decrypt(self, pyfile):
        self.prepare()
        self.check_info()  #@TODO: Remove in 0.4.10

        if self.direct_dl:
            self.log_debug(_("Looking for direct download link..."))
            self.handle_direct(pyfile)

            if self.link or self.links or self.urls or self.packages:
                self.log_info(_("Direct download link detected"))
            else:
                self.log_info(_("Direct download link not found"))

        if not (self.link or self.links or self.urls or self.packages):
            self.preload()

            self.links = self.get_links() or list()

            if self.PAGES_PATTERN:
                self.handle_pages(pyfile)

        if self.link:
            self.urls.append(self.link)

        if self.links:
            name = folder = pyfile.name
            self.packages.append((name, self.links, folder))


    def get_links(self):
        """
        Returns the links extracted from self.html
        You should override this only if it's impossible to extract links using only the LINK_PATTERN.
        """
        return re.findall(self.LINK_PATTERN, self.html)


    def load_page(self, number):
        raise NotImplementedError


    def handle_pages(self, pyfile):
        try:
            pages = int(re.search(self.PAGES_PATTERN, self.html).group(1))

        except Exception:
            pages = 1

        for p in xrange(2, pages + 1):
            self.html = self.load_page(p)
            self.links += self.get_links()
