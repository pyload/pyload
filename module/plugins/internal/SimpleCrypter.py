# -*- coding: utf-8 -*-

import re

from module.network.HTTPRequest import BadHeader
from module.network.RequestFactory import getURL as get_url
from module.plugins.internal.Crypter import Crypter, create_getInfo, parse_fileInfo
from module.plugins.internal.utils import replace_patterns, set_cookie, set_cookies


class SimpleCrypter(Crypter):
    __name__    = "SimpleCrypter"
    __type__    = "crypter"
    __version__ = "0.77"
    __status__  = "testing"

    __pattern__ = r'^unmatchable$'
    __config__  = [("activated"            , "bool", "Activated"                                        , True),
                   ("use_premium"          , "bool", "Use premium account if available"                 , True),
                   ("use_subfolder"        , "bool", "Save package to subfolder"                        , True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package"              , True),
                   ("max_wait"             , "int" , "Reconnect if waiting time is greater than minutes", 10  )]

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
    TEXT_ENCODING        = True   #: Set to encoding name if encoding value in http header is not correct

    LINK_PATTERN         = None
    LINK_FREE_PATTERN    = None
    LINK_PREMIUM_PATTERN = None
    PAGES_PATTERN        = None

    NAME_PATTERN         = None
    OFFLINE_PATTERN      = None
    TEMP_OFFLINE_PATTERN = None

    WAIT_PATTERN         = None
    PREMIUM_ONLY_PATTERN = None
    IP_BLOCKED_PATTERN   = None
    SIZE_LIMIT_PATTERN   = None
    ERROR_PATTERN        = None


    @classmethod
    def api_info(cls, url):
        return {}


    @classmethod
    def get_info(cls, url="", html=""):
        info = super(SimpleCrypter, cls).get_info(url)

        info.update(cls.api_info(url))

        if not html and info['status'] is not 2:
            if not url:
                info['error']  = "missing url"
                info['status'] = 1

            elif info['status'] is 3:
                try:
                    html = get_url(url, cookies=cls.COOKIES, decode=cls.TEXT_ENCODING)

                except BadHeader, e:
                    info['error'] = "%d: %s" % (e.code, e.content)

                except Exception:
                    pass

        if html:
            if cls.OFFLINE_PATTERN and re.search(cls.OFFLINE_PATTERN, html) is not None:
                info['status'] = 1

            elif cls.TEMP_OFFLINE_PATTERN and re.search(cls.TEMP_OFFLINE_PATTERN, html) is not None:
                info['status'] = 6

            elif cls.NAME_PATTERN:
                m = re.search(cls.NAME_PATTERN, html)
                if m is not None:
                    info['status'] = 2
                    info['pattern'].update(m.groupdict())

        if 'N' in info['pattern']:
            name = replace_patterns(info['pattern']['N'], cls.NAME_REPLACEMENTS)
            info['name'] = parse_name(name)

        return info


    #@TODO: Remove in 0.4.10
    def setup_base(self):
        account_name = self.classname.rsplit("Folder", 1)[0]

        if self.account:
            self.req     = self.pyload.requestFactory.getRequest(account_name, self.account.user)
            self.premium = self.account.info['data']['premium']  #@NOTE: Avoid one unnecessary get_info call by `self.account.premium` here
        else:
            self.req     = self.pyload.requestFactory.getRequest(account_name)
            self.premium = False

        super(SimpleCrypter, self).setup_base()


    #@TODO: Remove in 0.4.10
    def load_account(self):
        class_name = self.classname
        self.__class__.__name__ = class_name.rsplit("Folder", 1)[0]
        super(SimpleCrypter, self).load_account()
        self.__class__.__name__ = class_name


    def handle_direct(self, pyfile):
        link      = None
        maxredirs = self.get_config("maxredirs", default=10, plugin="UserAgentSwitcher")

        for i in xrange(maxredirs):
            url = link or pyfile.url
            self.log_debug("Redirect #%d to: %s" % (i, url))

            header   = self.load(url, just_header=True)
            location = header.get('location')

            if location:
                link = location

            elif link:
                self.urls.append(link)
                return
        else:
            self.log_warning(_("Too many redirects"))


    def preload(self):
        self.data = self.load(self.pyfile.url,
                              cookies=self.COOKIES,
                              ref=False,
                              decode=self.TEXT_ENCODING)


    def prepare(self):
        self.direct_dl = False

        if self.LOGIN_PREMIUM and not self.premium:
            self.fail(_("Required premium account not found"))

        if self.LOGIN_ACCOUNT and not self.account:
            self.fail(_("Required account not found"))

        self.req.setOption("timeout", 120)

        if self.LINK_PATTERN:
            if self.LINK_FREE_PATTERN is None:
                self.LINK_FREE_PATTERN = self.LINK_PATTERN

            if self.LINK_PREMIUM_PATTERN is None:
                self.LINK_PREMIUM_PATTERN = self.LINK_PATTERN

        if self.DIRECT_LINK is None:
            self.direct_dl = bool(self.account)
        else:
            self.direct_dl = self.DIRECT_LINK

        self.pyfile.url = replace_patterns(self.pyfile.url, self.URL_REPLACEMENTS)


    def decrypt(self, pyfile):
        self.prepare()

        if self.direct_dl:
            self.log_info(_("Looking for direct link..."))
            self.handle_direct(pyfile)

            if self.urls or self.packages:
                self.log_info(_("Direct link detected"))
            else:
                self.log_info(_("Direct link not found"))

        if not self.urls and not self.packages:
            self.preload()
            self.check_errors()

            self.urls.extend(self.get_links())

            if self.PAGES_PATTERN:
                self.handle_pages(pyfile)


    def handle_free(self, pyfile):
        if not self.LINK_FREE_PATTERN:
            self.log_warning(_("Free decrypting not implemented"))

        links = re.findall(self.LINK_FREE_PATTERN, self.data)
        if not links:
            self.error(_("Free decrypted link not found"))
        else:
            self.urls.extend(links)


    def handle_premium(self, pyfile):
        if not self.LINK_PREMIUM_PATTERN:
            self.log_warning(_("Premium decrypting not implemented"))
            self.restart(premium=False)

        links = re.findall(self.LINK_PREMIUM_PATTERN, self.data)
        if not links:
            self.error(_("Premium decrypted link found"))
        else:
            self.urls.extend(links)


    def get_links(self):
        """
        Returns the links extracted from self.data
        You should override this only if it's impossible to extract links using only the LINK_PATTERN.
        """
        if self.premium:
            self.log_info(_("Decrypting as premium link..."))
            self.handle_premium(pyfile)

        elif not self.LOGIN_ACCOUNT:
            self.log_info(_("Decrypting as free link..."))
            self.handle_free(pyfile)

        return self.urls


    def load_page(self, number):
        raise NotImplementedError


    def handle_pages(self, pyfile):
        try:
            pages = int(re.search(self.PAGES_PATTERN, self.data).group(1))

        except Exception:
            pages = 1

        for p in xrange(2, pages + 1):
            self.data = self.load_page(p)
            self.urls.extend(self.get_links())


    def check_errors(self):
        if not self.data:
            self.log_debug("No data to check")
            return

        if self.IP_BLOCKED_PATTERN and re.search(self.IP_BLOCKED_PATTERN, self.data):
            self.fail(_("Connection from your current IP address is not allowed"))

        elif not self.premium:
            if self.PREMIUM_ONLY_PATTERN and re.search(self.PREMIUM_ONLY_PATTERN, self.data):
                self.fail(_("Link can be decrypted by premium users only"))

            elif self.SIZE_LIMIT_PATTERN and re.search(self.SIZE_LIMIT_PATTERN, self.data):
                self.fail(_("Link list too large for free decrypt"))

        if self.ERROR_PATTERN:
            m = re.search(self.ERROR_PATTERN, self.data)
            if m is not None:
                try:
                    errmsg = m.group(1)

                except (AttributeError, IndexError):
                    errmsg = m.group(0)

                finally:
                    errmsg = re.sub(r'<.*?>', " ", errmsg.strip())

                self.info['error'] = errmsg
                self.log_warning(errmsg)

                if re.search('limit|wait|slot', errmsg, re.I):
                    wait_time = parse_time(errmsg)
                    self.wait(wait_time, reconnect=wait_time > self.get_config("max_wait", 10) * 60)
                    self.restart(_("Download limit exceeded"))

                elif re.search('country|ip|region|nation', errmsg, re.I):
                    self.fail(_("Connection from your current IP address is not allowed"))

                elif re.search('captcha|code', errmsg, re.I):
                    self.retry_captcha()

                elif re.search('countdown|expired', errmsg, re.I):
                    self.retry(10, 60, _("Link expired"))

                elif re.search('maint(e|ai)nance|temp', errmsg, re.I):
                    self.temp_offline()

                elif re.search('up to|size', errmsg, re.I):
                    self.fail(_("Link list too large for free decrypt"))

                elif re.search('offline|delet|remov|not? (found|(longer)? available)', errmsg, re.I):
                    self.offline()

                elif re.search('filename', errmsg, re.I):
                    self.fail(_("Invalid url"))

                elif re.search('premium', errmsg, re.I):
                    self.fail(_("Link can be decrypted by premium users only"))

                else:
                    self.wait(60, reconnect=True)
                    self.restart(errmsg)

        elif self.WAIT_PATTERN:
            m = re.search(self.WAIT_PATTERN, self.data)
            if m is not None:
                try:
                    waitmsg = m.group(1).strip()

                except (AttributeError, IndexError):
                    waitmsg = m.group(0).strip()

                wait_time = parse_time(waitmsg)
                self.wait(wait_time, reconnect=wait_time > self.get_config("max_wait", 10) * 60)

        self.info.pop('error', None)
