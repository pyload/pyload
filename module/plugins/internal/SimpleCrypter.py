# -*- coding: utf-8 -*-

import re

from module.plugins.internal.Crypter import Crypter, create_getInfo, parse_fileInfo
from module.plugins.internal.Plugin import replace_patterns, set_cookie, set_cookies


class SimpleCrypter(Crypter):
    __name__    = "SimpleCrypter"
    __type__    = "crypter"
    __version__ = "0.70"
    __status__  = "testing"

    __pattern__ = r'^unmatchable$'
    __config__  = [("activated"            , "bool", "Activated"                          , True),
                   ("use_premium"          , "bool", "Use premium account if available"   , True),
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
    HAPPY_HOUR_PATTERN   = None
    IP_BLOCKED_PATTERN   = None
    DL_LIMIT_PATTERN     = None
    SIZE_LIMIT_PATTERN   = None
    ERROR_PATTERN        = None


     @classmethod
    def api_info(cls, url):
        return {}


    @classmethod
    def get_info(cls, url="", html=""):
        info = super(SimpleHoster, cls).get_info(url)

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

                    if e.code is 404:
                        info['status'] = 1

                    elif e.code is 503:
                        info['status'] = 6

                except Exception:
                    pass

        if html:
            if cls.OFFLINE_PATTERN and re.search(cls.OFFLINE_PATTERN, html) is not None:
                info['status'] = 1

            elif cls.TEMP_OFFLINE_PATTERN and re.search(cls.TEMP_OFFLINE_PATTERN, html) is not None:
                info['status'] = 6

            elif cls.NAME_PATTERN:
                m = re.search(cls.NAME_PATTERN, html):
                if m is not None:
                    info['status'] = 2
                    info['pattern'].update(m.groupdict())

        if 'N' in info['pattern']:
            name = replace_patterns(info['pattern']['N'], cls.NAME_REPLACEMENTS)
            info['name'] = parse_name(name)

        return info


    #@TODO: Remove in 0.4.10
    def _setup(self):
        orig_name     = self.classname
        self.classname = orig_name.rstrip("Folder")
        super(SimpleCrypter, self)._setup()
        self.classname = orig_name


    #@TODO: Remove in 0.4.10
    def load_account(self):
        orig_name     = self.classname
        self.classname = orig_name.rstrip("Folder")
        super(SimpleCrypter, self).load_account()
        self.classname = orig_name


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


    def preload(self):
        self.html = self.load(self.pyfile.url,
                              cookies=self.COOKIES,
                              ref=False,
                              decode=self.TEXT_ENCODING)


    def prepare(self):
        self.link      = ""
        self.links     = []
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
        self.check_info()  #@TODO: Remove in 0.4.10

        if self.direct_dl:
            self.log_debug(_("Looking for direct link..."))
            self.handle_direct(pyfile)

            if self.link or self.links or self.urls or self.packages:
                self.log_info(_("Direct link detected"))
            else:
                self.log_info(_("Direct link not found"))

        if not (self.link or self.links or self.urls or self.packages):
            self.preload()

            self.links.extend(self.get_links())

            if self.PAGES_PATTERN:
                self.handle_pages(pyfile)

        if self.link:
            self.urls.append(self.link)

        if self.links:
            self.packages.append((pyfile.name, self.links, pyfile.name))


    def handle_free(self, pyfile):
        if not self.LINK_FREE_PATTERN:
            self.log_error(_("Free decrypting not implemented"))

        links = re.findall(self.LINK_FREE_PATTERN, self.html)
        if not links:
            self.error(_("Free decrypted link not found"))
        else:
            self.links.extend(links)


    def handle_premium(self, pyfile):
        if not self.LINK_PREMIUM_PATTERN:
            self.log_error(_("Premium decrypting not implemented"))
            self.restart(premium=False)

        links = re.findall(self.LINK_PREMIUM_PATTERN, self.html)
        if not links:
            self.error(_("Premium decrypted link found"))
        else:
            self.links.extend(links)


    def get_links(self):
        """
        Returns the links extracted from self.html
        You should override this only if it's impossible to extract links using only the LINK_PATTERN.
        """
        if self.premium:
            self.log_info(_("Decrypting as premium link..."))
            self.handle_premium(pyfile)

        elif not self.LOGIN_ACCOUNT:
            self.log_info(_("Decrypting as free link..."))
            self.handle_free(pyfile)

        return self.links


    def load_page(self, number):
        raise NotImplementedError


    def handle_pages(self, pyfile):
        try:
            pages = int(re.search(self.PAGES_PATTERN, self.html).group(1))

        except Exception:
            pages = 1

        for p in xrange(2, pages + 1):
            self.html = self.load_page(p)
            self.links.append(self.get_links())


    def check_errors(self):
        if not self.html:
            self.log_warning(_("No html code to check"))
            return

        if self.IP_BLOCKED_PATTERN and re.search(self.IP_BLOCKED_PATTERN, self.html):
            self.fail(_("Connection from your current IP address is not allowed"))

        elif not self.premium:
            if self.PREMIUM_ONLY_PATTERN and re.search(self.PREMIUM_ONLY_PATTERN, self.html):
                self.fail(_("Link can be decrypted by premium users only"))

            elif self.SIZE_LIMIT_PATTERN and re.search(self.SIZE_LIMIT_PATTERN, self.html):
                self.fail(_("Link list too large for free decrypt"))

            elif self.DL_LIMIT_PATTERN and re.search(self.DL_LIMIT_PATTERN, self.html):
                m = re.search(self.DL_LIMIT_PATTERN, self.html)
                try:
                    errmsg = m.group(1).strip()

                except (AttributeError, IndexError):
                    errmsg = m.group(0).strip()

                finally:
                    errmsg = re.sub(r'<.*?>', " ", errmsg)

                self.info['error'] = errmsg
                self.log_warning(errmsg)

                wait_time = parse_time(errmsg)
                self.wait(wait_time, reconnect=wait_time > 300)
                self.restart(_("Download limit exceeded"))

        if self.HAPPY_HOUR_PATTERN and re.search(self.HAPPY_HOUR_PATTERN, self.html):
            self.multiDL = True

        if self.ERROR_PATTERN:
            m = re.search(self.ERROR_PATTERN, self.html)
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
                    self.wait(wait_time, reconnect=wait_time > 300)
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
            m = re.search(self.WAIT_PATTERN, self.html)
            if m is not None:
                try:
                    waitmsg = m.group(1).strip()

                except (AttributeError, IndexError):
                    waitmsg = m.group(0).strip()

                wait_time = parse_time(waitmsg)
                self.wait(wait_time, reconnect=wait_time > 300)

        self.info.pop('error', None)


    def check_status(self, getinfo=True):
        if not self.info or getinfo:
            self.log_info(_("Updating file info..."))
            old_info = self.info.copy()
            self.info.update(self.get_info(self.pyfile.url, self.html))
            self.log_debug("File info: %s" % self.info)
            self.log_debug("Previous file info: %s" % old_info)

        try:
            status = self.info['status'] or 14

            if status is 1:
                self.offline()

            elif status is 6:
                self.temp_offline()

            elif status is 8:
                self.fail()

        finally:
            self.log_info(_("File status: ") + self.pyfile.getStatusName())


    def check_name_folder(self, getinfo=True):
        if not self.info or getinfo:
            self.log_info(_("Updating file info..."))
            old_info = self.info.copy()
            self.info.update(self.get_info(self.pyfile.url, self.html))
            self.log_debug("File info: %s" % self.info)
            self.log_debug("Previous file info: %s" % old_info)

        name   = self.info.get('name')
        folder = self.info.get('folder')

        if name and name is not self.info.get('url'):
            self.pyfile.name = name
        else:
            name = self.pyfile.name

        self.info['folder'] = folder else self.pyfile.name

        self.log_info(_("File name: ") + name)
        self.log_info(_("File folder: ") + folder)


    #@TODO: Rewrite in 0.4.10
    def check_info(self):
        self.check_name_folder()

        if self.html:
            self.check_errors()
            self.check_name_folder()

        self.check_status(getinfo=False)
