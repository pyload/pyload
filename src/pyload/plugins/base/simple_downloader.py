# -*- coding: utf-8 -*-
import os
import re

from pyload.core.network.http.exceptions import BadHeader
from pyload.core.utils import parse

from ..helpers import replace_patterns, search_pattern
from .downloader import BaseDownloader


class SimpleDownloader(BaseDownloader):
    __name__ = "SimpleDownloader"
    __type__ = "downloader"
    __version__ = "2.42"
    __status__ = "stable"

    __pattern__ = r"^unmatchable$"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Simple downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    """
    Info patterns:

      INFO_PATTERN: (mandatory) Name and Size of the file
        example: INFO_PATTERN = r'(?P<N>file_name) (?P<S>file_size) (?P<U>size_unit)'
      or
        NAME_PATTERN: (mandatory) Name that will be set for the file
          example: NAME_PATTERN = r'(?P<N>file_name)'

        SIZE_PATTERN: (mandatory) Size that will be checked for the file
          example: SIZE_PATTERN = r'(?P<S>file_size) (?P<U>size_unit)'

      HASHSUM_PATTERN: (optional) Hash code and type of the file
        example: HASHSUM_PATTERN = r'(?P<D>hash_digest) (?P<H>MD5)'

      OFFLINE_PATTERN: (mandatory) Check if the page is unreachable
        example: OFFLINE_PATTERN = r'File (deleted|not found)'

      TEMP_OFFLINE_PATTERN: (optional) Check if the page is temporarily unreachable
        example: TEMP_OFFLINE_PATTERN = r'Server (maintenance|maintainance)'


    Error patterns:

      WAIT_PATTERN: (optional) Detect waiting time
        example: WAIT_PATTERN = r''

      PREMIUM_ONLY_PATTERN: (optional) Check if the file can be downloaded only with a premium account
        example: PREMIUM_ONLY_PATTERN = r'Premium account required'

      HAPPY_HOUR_PATTERN: (optional)
        example: HAPPY_HOUR_PATTERN = r'Happy hour'

      IP_BLOCKED_PATTERN: (optional)
        example: IP_BLOCKED_PATTERN = r'in your country'

      DL_LIMIT_PATTERN: (optional)
        example: DL_LIMIT_PATTERN = r'download limit'

      SIZE_LIMIT_PATTERN: (optional)
        example: SIZE_LIMIT_PATTERN = r'up to'

      ERROR_PATTERN: (optional) Detect any error preventing download
        example: ERROR_PATTERN = r''


    Instead overriding handle_free and handle_premium methods you may define the following patterns for basic link handling:

      LINK_PATTERN: (optional) group(1) should be the direct link for free and premium download
        example: LINK_PATTERN = r'<div class="link"><a href="(.+?)"'
      or
        LINK_FREE_PATTERN: (optional) group(1) should be the direct link for free download
          example: LINK_FREE_PATTERN = r'<div class="link"><a href="(.+?)"'

        LINK_PREMIUM_PATTERN: (optional) group(1) should be the direct link for premium download
          example: LINK_PREMIUM_PATTERN = r'<div class="link"><a href="(.+?)"'
    """
    NAME_REPLACEMENTS = []
    SIZE_REPLACEMENTS = []
    URL_REPLACEMENTS = []

    #: Set to False to not check the last downloaded file with declared error patterns
    CHECK_FILE = True
    CHECK_TRAFFIC = (
        False  #: Set to True to reload checking traffic left for premium account
    )
    COOKIES = True  #: or False or list of tuples [(domain, name, value)]
    #: Set to True to looking for direct link (as defined in handle_direct method), set to None to do it if self.account is True else False
    DIRECT_LINK = True
    #: Set to True to use any content-disposition value found in http header as file name
    DISPOSITION = True
    LOGIN_ACCOUNT = False  #: Set to True to require account login
    LOGIN_PREMIUM = False  #: Set to True to require premium account login
    #: Set to encoding name if encoding value in http header is not correct
    TEXT_ENCODING = True
    # TRANSLATE_ERROR      = True

    LINK_PATTERN = None
    LINK_FREE_PATTERN = None
    LINK_PREMIUM_PATTERN = None

    INFO_PATTERN = None
    NAME_PATTERN = None
    SIZE_PATTERN = None
    HASHSUM_PATTERN = r"[^\w](?P<H>(CRC|crc)(-?32)?|(MD|md)-?5|(SHA|sha)-?(1|224|256|384|512)).*(:|=|>)[ ]*(?P<D>(?:[a-z0-9]|[A-Z0-9]){8,})"
    OFFLINE_PATTERN = (
        r"[^\w](?:404\s|[Nn]ot [Ff]ound|[Ff]ile (?:was|has been)?\s*(?:removed|deleted)|[Ff]ile (?:does not exist|could not be found|no longer available))"
    )
    TEMP_OFFLINE_PATTERN = (
        r"[^\w](?:503\s|[Ss]erver (?:is (?:in|under) )?[Mm]aint(?:e|ai)nance|[Tt]emp(?:[.-]|orarily )(?:[Oo]ffline|[Uu]available)|[Uu]se (?:[Aa] )?[Mm]irror)"
    )

    WAIT_PATTERN = None
    PREMIUM_ONLY_PATTERN = None
    HAPPY_HOUR_PATTERN = None
    IP_BLOCKED_PATTERN = None
    DL_LIMIT_PATTERN = None
    SIZE_LIMIT_PATTERN = None
    ERROR_PATTERN = None

    FILE_ERRORS = [
        (
            "Html error",
            rb"\A(?:\s*<.+>)?((?:[\w\s]*(?:[Ee]rror|ERROR)\s*\:?)?\s*\d{3})(?:\Z|\s+)",
        ),
        ("Request error", rb"([Aa]n error occurred while processing your request)"),
        ("Html file", rb"\A\s*<!DOCTYPE html"),
    ]

    def api_info(self, url):
        return {}

    def get_info(self, url="", html=""):
        info = super(SimpleDownloader, self).get_info(url)
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

        if html and info["status"] in (3, 7):
            if search_pattern(self.OFFLINE_PATTERN, html) is not None:
                info["status"] = 1

            elif search_pattern(self.TEMP_OFFLINE_PATTERN, html) is not None:
                info["status"] = 6

            else:
                for pattern in (
                    "INFO_PATTERN",
                    "NAME_PATTERN",
                    "SIZE_PATTERN",
                    "HASHSUM_PATTERN",
                ):
                    try:
                        attr = getattr(self, pattern)
                        pdict = search_pattern(attr, html).groupdict()

                        if all(True for k in pdict if k not in info["pattern"]):
                            info["pattern"].update(pdict)

                    except Exception:
                        continue

                    else:
                        info["status"] = 2

        if "N" in info["pattern"]:
            name = replace_patterns(info["pattern"]["N"], self.NAME_REPLACEMENTS)
            info["name"] = parse.name(name)

        if "S" in info["pattern"]:
            size = replace_patterns(
                info["pattern"]["S"] + info["pattern"]["U"]
                if "U" in info["pattern"]
                else info["pattern"]["S"],
                self.SIZE_REPLACEMENTS,
            )
            info["size"] = parse.bytesize(size)

        elif isinstance(info["size"], str):
            unit = info["units"] if "units" in info else None
            info["size"] = parse.bytesize(info["size"], unit)

        if "H" in info["pattern"]:
            hash_type = info["pattern"]["H"].strip("-").upper()
            info["hash"][hash_type] = info["pattern"]["D"]

        return info

    def setup(self):
        self.multi_dl = self.premium
        self.resume_download = self.premium

    def _prepare(self):
        self.link = ""
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

    def _preload(self):
        if self.data:
            return

        self.data = self.load(
            self.pyfile.url, cookies=self.COOKIES, ref=False, decode=self.TEXT_ENCODING
        )

    def process(self, pyfile):
        self._prepare()

        if not self.link and self.direct_dl:
            self.log_info(self._("Looking for direct download link..."))
            self.handle_direct(pyfile)

            if self.link:
                self.log_info(self._("Direct download link detected"))
            else:
                self.log_info(self._("Direct download link not found"))

        if not self.link:
            self._preload()
            self.check_errors()

            if self.info.get("status", 7) != 2:
                super(SimpleDownloader, self).grab_info()
                self.check_status()
                self.pyfile.set_status("starting")
                self.check_duplicates()

            out_of_traffic = self.CHECK_TRAFFIC and self.out_of_traffic()
            if self.premium and not out_of_traffic:
                self.log_info(self._("Processing as premium download..."))
                self.handle_premium(pyfile)

            elif not self.LOGIN_ACCOUNT or not out_of_traffic:
                self.log_info(self._("Processing as free download..."))
                self.handle_free(pyfile)

        if self.link and not self.last_download:
            self.log_info(self._("Downloading file..."))
            self.download(self.link, disposition=self.DISPOSITION)

    def _check_download(self):
        super()._check_download()
        self.check_download()

    def check_download(self):
        self.log_info(self._("Checking file (with built-in rules)..."))
        for r, p in self.FILE_ERRORS:
            errmsg = self.scan_download({r: re.compile(p)})
            if errmsg is not None:
                errmsg = errmsg.strip().capitalize()

                try:
                    errmsg += " | " + self.last_check.group(1).strip()

                except Exception:
                    pass

                self.log_warning(
                    self._("Check result: ") + errmsg,
                    self._("Waiting 1 minute and retry"),
                )
                self.wait(60, reconnect=True)
                self.restart(errmsg)
        else:
            if self.CHECK_FILE:
                self.log_info(self._("Checking file (with custom rules)..."))

                try:
                    with open(os.fsdecode(self.last_download), mode="r", encoding='utf-8') as fp:
                        self.data = fp.read(1_048_576)  # TODO: Recheck in 0.6.x

                except UnicodeDecodeError:
                    with open(os.fsdecode(self.last_download), mode="r", encoding='iso-8859-1') as fp:
                        self.data = fp.read(1_048_576)  # TODO: Recheck in 0.6.x

                self.check_errors()

            else:
                self.log_info(self._("No errors found"))

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
                self.fail(self._("File can be downloaded by premium users only"))

            elif search_pattern(self.SIZE_LIMIT_PATTERN, data):
                self.fail(self._("File too large for free download"))

            elif self.DL_LIMIT_PATTERN:
                m = search_pattern(self.DL_LIMIT_PATTERN, data)
                if m is not None:
                    try:
                        errmsg = m.group(1)

                    except (AttributeError, IndexError):
                        errmsg = m.group(0)

                    finally:
                        errmsg = re.sub(r"<.*?>", " ", errmsg.strip())

                    self.info["error"] = errmsg
                    self.log_warning(errmsg)

                    wait_time = parse.seconds(errmsg)
                    self.wait(
                        wait_time,
                        reconnect=wait_time > self.config.get("max_wait", 10) * 60,
                    )
                    self.restart(self._("Download limit exceeded"))

        if search_pattern(self.HAPPY_HOUR_PATTERN, data):
            self.multi_dl = True

        if self.ERROR_PATTERN:
            m = search_pattern(self.ERROR_PATTERN, data)
            if m is not None:
                try:
                    errmsg = m.group(1).strip()

                except (AttributeError, IndexError):
                    errmsg = m.group(0).strip()

                finally:
                    errmsg = re.sub(r"<.*?>", " ", errmsg)

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
                    self.fail(self._("File too large for free download"))

                elif re.search(
                    r"404|sorry|offline|delet|remov|(no(t|thing)?|sn\'t) (found|(longer )?(available|exist))",
                    errmsg,
                    re.I,
                ):
                    self.offline()

                elif re.search(r"filename", errmsg, re.I):
                    self.fail(self._("Invalid url"))

                elif re.search(r"premium", errmsg, re.I):
                    self.fail(self._("File can be downloaded by premium users only"))

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

    #: Deprecated method (Remove in 0.6.x)
    def get_file_info(self):
        self.info.clear()
        self.grab_info()
        return self.info

    def grab_info(self):
        if self.info.get("status", 7) != 2:
            self.pyfile.name = parse.name(self.pyfile.url)

    def handle_direct(self, pyfile):
        link = self.isresource(pyfile.url)
        if link:
            pyfile.name = parse.name(link)
            self.link = pyfile.url

        else:
            self.link = None

    def handle_free(self, pyfile):
        if not self.LINK_FREE_PATTERN:
            self.fail(self._("Free download not implemented"))

        m = search_pattern(self.LINK_FREE_PATTERN, self.data)
        if m is None:
            self.error(self._("Free download link not found"))
        else:
            self.link = m.group(1)

    def handle_premium(self, pyfile):
        if not self.LINK_PREMIUM_PATTERN:
            self.log_warning(self._("Premium download not implemented"))
            self.restart(premium=False)

        m = search_pattern(self.LINK_PREMIUM_PATTERN, self.data)
        if m is None:
            self.error(self._("Premium download link not found"))
        else:
            self.link = m.group(1)
