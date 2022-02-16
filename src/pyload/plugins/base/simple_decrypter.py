# -*- coding: utf-8 -*-

import re

from pyload.core.network.http.exceptions import BadHeader
from pyload.core.utils import parse

from ..helpers import replace_patterns, search_pattern
from .decrypter import BaseDecrypter


class SimpleDecrypter(BaseDecrypter):
    __name__ = "SimpleDecrypter"
    __type__ = "decrypter"
    __version__ = "0.98"
    __status__ = "testing"

    __pattern__ = r"^unmatchable$"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        (
            "folder_per_package",
            "Default;Yes;No",
            "Create folder for each package",
            "Default",
        ),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Simple decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    """
    Following patterns should be defined by each decrypter:

      LINK_PATTERN: Download link or regex to catch links in group(1)
        example: LINK_PATTERN = r'<div class="link"><a href="(.+?)"'

      NAME_PATTERN: (optional) folder name or page title
        example: NAME_PATTERN = r'<title>Files of: (?P<N>.+?) folder</title>'

      OFFLINE_PATTERN: (optional) Checks if the page is unreachable
        example: OFFLINE_PATTERN = r'File (deleted|not found)'

      TEMP_OFFLINE_PATTERN: (optional) Checks if the page is temporarily unreachable
        example: TEMP_OFFLINE_PATTERN = r'Server maintainance'


    You can override the get_links method if you need a more sophisticated way to extract the links.


    If the links are splitted on multiple pages you can define the PAGES_PATTERN regex:

      PAGES_PATTERN: (optional) group(1) should be the number of overall pages containing the links
        example: PAGES_PATTERN = r'Pages: (\d+)'

    and its load_page method:

      def load_page(self, page_n):
          return the html of the page number page_n
    """
    NAME_REPLACEMENTS = []
    URL_REPLACEMENTS = []

    COOKIES = True  #: or False or list of tuples [(domain, name, value)]
    #: Set to True to looking for direct link (as defined in handle_direct method), set to None to do it if self.account is True else False
    DIRECT_LINK = True
    LOGIN_ACCOUNT = False  #: Set to True to require account login
    LOGIN_PREMIUM = False  #: Set to True to require premium account login
    #: Set to encoding name if encoding value in http header is not correct
    TEXT_ENCODING = True

    LINK_PATTERN = None
    LINK_FREE_PATTERN = None
    LINK_PREMIUM_PATTERN = None
    PAGES_PATTERN = None

    NAME_PATTERN = None
    OFFLINE_PATTERN = (
        r"[^\w](?:404\s|[Nn]ot [Ff]ound|[Ff]ile (?:was|has been)?\s*(?:removed|deleted)|[Ff]ile (?:does not exist|could not be found|no longer available))"
    )
    TEMP_OFFLINE_PATTERN = (
        r"[^\w](?:503\s|[Ss]erver (?:is (?:in|under) )?[Mm]aint(?:e|ai)nance|[Tt]emp(?:[.-]|orarily )(?:[Oo]ffline|[Uu]available)|[Uu]se (?:[Aa] )?[Mm]irror)"
    )

    WAIT_PATTERN = None
    PREMIUM_ONLY_PATTERN = None
    IP_BLOCKED_PATTERN = None
    SIZE_LIMIT_PATTERN = None
    ERROR_PATTERN = None

    def api_info(self, url):
        return {}

    def get_info(self, url="", html=""):
        info = super(SimpleDecrypter, self).get_info(url)

        info.update(self.api_info(url))

        if not html and info["status"] != 2:
            if not url:
                info["error"] = "missing url"
                info["status"] = 1

            elif info["status"] in (3, 7):
                try:
                    html = self.load(url, cookies=self.COOKIES, decode=self.TEXT_ENCODING)

                except BadHeader as exc:
                    info["error"] = "{}: {}".format(exc.code, exc.content)

                except Exception:
                    pass

        if html:
            if search_pattern(self.OFFLINE_PATTERN, html) is not None:
                info["status"] = 1

            elif search_pattern(self.TEMP_OFFLINE_PATTERN, html) is not None:
                info["status"] = 6

            elif self.NAME_PATTERN:
                m = search_pattern(self.NAME_PATTERN, html)
                if m is not None:
                    info["status"] = 2
                    info["pattern"].update(m.groupdict())

        if "N" in info["pattern"]:
            name = replace_patterns(info["pattern"]["N"], self.NAME_REPLACEMENTS)
            info["name"] = parse.name(name)

        return info

    # TODO: Remove in 0.6.x
    def setup_base(self):
        account_name = self.classname.rsplit("Folder", 1)[0]

        if self.account:
            self.req = self.pyload.request_factory.get_request(
                account_name, self.account.user
            )
            # NOTE: Don't call get_info here to reduce overhead
            self.premium = self.account.info["data"]["premium"]
        else:
            self.req = self.pyload.request_factory.get_request(account_name)
            self.premium = False

        super().setup_base()

    # TODO: Remove in 0.6.x
    def load_account(self):
        class_name = self.classname
        self.__class__.__name__ = class_name.rsplit("Folder", 1)[0]
        super().load_account()
        self.__class__.__name__ = class_name

    def handle_direct(self, pyfile):
        self._preload()

        link = self.last_header.get("url")
        if re.match(self.__pattern__, link) is None:
            self.links.append(link)

    def _preload(self):
        if self.data:
            return

        self.data = self.load(
            self.pyfile.url, cookies=self.COOKIES, ref=False, decode=self.TEXT_ENCODING
        )

    def _prepare(self):
        self.direct_dl = False

        if self.LOGIN_PREMIUM:
            self.no_fallback = True
            if not self.premium:
                self.fail(self._("Required premium account not found"))

        if self.LOGIN_ACCOUNT and not self.account:
            self.fail(self._("Required account not found"))

        self.req.set_option("timeout", 120)

        if self.LINK_PATTERN:
            if self.LINK_FREE_PATTERN is None:
                self.LINK_FREE_PATTERN = self.LINK_PATTERN

            if self.LINK_PREMIUM_PATTERN is None:
                self.LINK_PREMIUM_PATTERN = self.LINK_PATTERN

        if self.DIRECT_LINK is None:
            self.direct_dl = bool(self.premium)
        else:
            self.direct_dl = self.DIRECT_LINK

        self.pyfile.url = replace_patterns(self.pyfile.url, self.URL_REPLACEMENTS)

    def decrypt(self, pyfile):
        self._prepare()

        if self.direct_dl:
            self.log_info(self._("Looking for direct link..."))
            self.handle_direct(pyfile)

            if self.links or self.packages:
                self.log_info(self._("Direct link detected"))
            else:
                self.log_info(self._("Direct link not found"))

        if not self.links and not self.packages:
            self._preload()
            self.check_errors()

            links = self.get_links()
            self.links.extend(links)

            if self.PAGES_PATTERN:
                self.handle_pages(pyfile)

    def handle_free(self, pyfile):
        if not self.LINK_FREE_PATTERN:
            self.log_warning(self._("Free decrypting not implemented"))

        links = re.findall(self.LINK_FREE_PATTERN, self.data)
        if not links:
            self.error(self._("Free decrypted link not found"))
        else:
            self.links.extend(links)

    def handle_premium(self, pyfile):
        if not self.LINK_PREMIUM_PATTERN:
            self.log_warning(self._("Premium decrypting not implemented"))
            self.restart(premium=False)

        links = re.findall(self.LINK_PREMIUM_PATTERN, self.data)
        if not links:
            self.error(self._("Premium decrypted link found"))
        else:
            self.links.extend(links)

    def get_links(self):
        """
        Returns the links extracted from self.data You should override this only if it's
        impossible to extract links using only the LINK_PATTERN.
        """
        if self.premium:
            self.log_info(self._("Decrypting as premium link..."))
            self.handle_premium(self.pyfile)

        elif not self.LOGIN_ACCOUNT:
            self.log_info(self._("Decrypting as free link..."))
            self.handle_free(self.pyfile)

        links = self.links
        self.links = []

        return links

    def load_page(self, number):
        raise NotImplementedError

    def handle_pages(self, pyfile):
        try:
            pages = int(search_pattern(self.PAGES_PATTERN, self.data).group(1))

        except (AttributeError, IndexError, ValueError):
            pages = 1

        links = self.links
        for p in range(2, pages + 1):
            self.data = self.load_page(p)
            links.extend(self.get_links())

        self.links = links

    def check_errors(self, data=None):
        self.log_info(self._("Checking for link errors..."))

        data = data or self.data

        if not data:
            self.log_warning(self._("No data to check"))
            return
        elif isinstance(data, bytes):
            self.log_debug(self._("No check on binary data"))
            return

        if search_pattern(self.IP_BLOCKED_PATTERN, data):
            self.fail(self._("Connection from your current IP address is not allowed"))

        elif not self.premium:
            if search_pattern(self.PREMIUM_ONLY_PATTERN, data):
                self.fail(self._("Link can be decrypted by premium users only"))

            elif search_pattern(self.SIZE_LIMIT_PATTERN, data):
                self.fail(self._("Link list too large for free decrypt"))

        if self.ERROR_PATTERN:
            m = search_pattern(self.ERROR_PATTERN, data)
            if m is not None:
                try:
                    errmsg = m.group(1)

                except (AttributeError, IndexError):
                    errmsg = m.group(0)

                finally:
                    errmsg = re.sub(r"<.*?>", " ", errmsg.strip())

                self.info["error"] = errmsg
                self.log_warning(errmsg)

                if search_pattern(self.TEMP_OFFLINE_PATTERN, errmsg):
                    self.temp_offline()

                elif search_pattern(self.OFFLINE_PATTERN, errmsg):
                    self.offline()

                elif re.search(r"limit|wait|slot", errmsg, re.I):
                    wait_time = parse.seconds(errmsg)
                    self.wait(
                        wait_time,
                        reconnect=wait_time > self.config.get("max_wait", 10) * 60,
                    )
                    self.restart(self._("Download limit exceeded"))

                elif re.search(r"country|ip|region|nation", errmsg, re.I):
                    self.fail(
                        self._("Connection from your current IP address is not allowed")
                    )

                elif re.search(r"captcha|code", errmsg, re.I):
                    self.retry_captcha()

                elif re.search(r"countdown|expired", errmsg, re.I):
                    self.retry(10, 60, self._("Link expired"))

                elif re.search(r"503|maint(e|ai)nance|temp|mirror", errmsg, re.I):
                    self.temp_offline()

                elif re.search(r"up to|size", errmsg, re.I):
                    self.fail(self._("Link list too large for free decrypt"))

                elif re.search(
                    r"404|sorry|offline|delet|remov|(no(t|thing)?|sn\'t) (found|(longer )?(available|exist))",
                    errmsg,
                    re.I,
                ):
                    self.offline()

                elif re.search(r"filename", errmsg, re.I):
                    self.fail(self._("Invalid url"))

                elif re.search(r"premium", errmsg, re.I):
                    self.fail(self._("Link can be decrypted by premium users only"))

                else:
                    self.wait(60, reconnect=True)
                    self.restart(errmsg)

        elif self.WAIT_PATTERN:
            m = search_pattern(self.WAIT_PATTERN, data)
            if m is not None:
                try:
                    waitmsg = m.group(1).strip()

                except (AttributeError, IndexError):
                    waitmsg = m.group(0).strip()

                wait_time = parse.seconds(waitmsg)
                self.wait(
                    wait_time,
                    reconnect=wait_time > self.config.get("max_wait", 10) * 60,
                )

        self.log_info(self._("No errors found"))
        self.info.pop("error", None)
