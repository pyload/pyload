# -*- coding: utf-8 -*-

from __future__ import with_statement

import re
import time

from module.network.HTTPRequest import BadHeader
from module.network.RequestFactory import getURL as get_url
from module.plugins.internal.Hoster import Hoster, create_getInfo, parse_fileInfo
from module.plugins.internal.Plugin import Fail
from module.plugins.internal.utils import (encode, parse_name, parse_size,
                                           parse_time, replace_patterns, seconds_to_midnight,
                                           set_cookie, set_cookies)


class SimpleHoster(Hoster):
    __name__    = "SimpleHoster"
    __type__    = "hoster"
    __version__ = "2.07"
    __status__  = "stable"

    __pattern__ = r'^unmatchable$'
    __config__  = [("activated"   , "bool", "Activated"                                        , True),
                   ("use_premium" , "bool", "Use premium account if available"                 , True),
                   ("fallback"    , "bool", "Fallback to free download if premium fails"       , True),
                   ("chk_filesize", "bool", "Check file size"                                  , True),
                   ("max_wait"    , "int" , "Reconnect if waiting time is greater than minutes", 10  )]

    __description__ = """Simple hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]

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
        example: HASHSUM_PATTERN = r'(?P<H>hash_code) (?P<T>MD5)'

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

    NAME_REPLACEMENTS    = []
    SIZE_REPLACEMENTS    = []
    URL_REPLACEMENTS     = []

    CHECK_FILE           = True   #: Set to False to not check the last downloaded file with declared error patterns
    CHECK_TRAFFIC        = False  #: Set to True to reload checking traffic left for premium account
    COOKIES              = True   #: or False or list of tuples [(domain, name, value)]
    DIRECT_LINK          = True   #: Set to True to looking for direct link (as defined in handle_direct method), set to None to do it if self.account is True else False
    DISPOSITION          = True   #: Set to True to use any content-disposition value in http header as file name
    LOGIN_ACCOUNT        = False  #: Set to True to require account login
    LOGIN_PREMIUM        = False  #: Set to True to require premium account login
    LEECH_HOSTER         = False  #: Set to True to leech other hoster link (as defined in handle_multi method)
    TEXT_ENCODING        = True   #: Set to encoding name if encoding value in http header is not correct

    LINK_PATTERN         = None
    LINK_FREE_PATTERN    = None
    LINK_PREMIUM_PATTERN = None

    INFO_PATTERN         = None
    NAME_PATTERN         = None
    SIZE_PATTERN         = None
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

    FILE_ERRORS          = [('Html error'   , r'\A(?:\s*<.+>)?((?:[\w\s]*(?:[Ee]rror|ERROR)\s*\:?)?\s*\d{3})(?:\Z|\s+)'),
                            ('Request error', r'([Aa]n error occured while processing your request)'                   ),
                            ('Html file'    , r'\A\s*<!DOCTYPE html'                                                   )]


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
                    if not self.isdownload(url):
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

            else:
                for pattern in ("INFO_PATTERN", "NAME_PATTERN", "SIZE_PATTERN", "HASHSUM_PATTERN"):
                    try:
                        attr  = getattr(cls, pattern)
                        pdict = re.search(attr, html).groupdict()

                        if all(True for k in pdict if k not in info['pattern']):
                            info['pattern'].update(pdict)

                    except Exception:
                        continue

                    else:
                        info['status'] = 2

        if 'N' in info['pattern']:
            name = replace_patterns(info['pattern']['N'], cls.NAME_REPLACEMENTS)
            info['name'] = parse_name(name)

        if 'S' in info['pattern']:
            size = replace_patterns(info['pattern']['S'] + info['pattern']['U'] if 'U' in info['pattern'] else info['pattern']['S'],
                                    cls.SIZE_REPLACEMENTS)
            info['size'] = parse_size(size)

        elif isinstance(info['size'], basestring):
            unit = info['units'] if 'units' in info else ""
            info['size'] = parse_size(info['size'], unit)

        if 'H' in info['pattern']:
            hashtype = info['pattern']['T'] if 'T' in info['pattern'] else "hash"
            info[hashtype] = info['pattern']['H']

        return info


    def setup(self):
        self.multiDL         = self.premium
        self.resume_download = self.premium


    def prepare(self):
        self.link      = ""
        self.direct_dl = False
        self.leech_dl  = False

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

        if self.LEECH_HOSTER:
            pattern = self.pyload.pluginManager.hosterPlugins[self.classname]['pattern']
            if self.__pattern__ is not pattern and re.match(self.__pattern__, self.pyfile.url) is None:
                self.leech_dl = True

        if self.leech_dl:
            self.direct_dl = False

        elif self.DIRECT_LINK is None:
            self.direct_dl = bool(self.account)

        else:
            self.direct_dl = self.DIRECT_LINK

        if not self.leech_dl:
            self.pyfile.url = replace_patterns(self.pyfile.url, self.URL_REPLACEMENTS)


    def preload(self):
        self.data = self.load(self.pyfile.url,
                              cookies=self.COOKIES,
                              ref=False,
                              decode=self.TEXT_ENCODING)


    def process(self, pyfile):
        self.prepare()

        if self.leech_dl:
            self.log_info(_("Processing as debrid download..."))
            self.handle_multi(pyfile)

            if not self.link and not was_downloaded():
                self.log_info(_("Failed to leech url"))

        else:
            if not self.link and self.direct_dl and not self.last_download:
                self.log_info(_("Looking for direct download link..."))
                self.handle_direct(pyfile)

                if self.link or self.last_download:
                    self.log_info(_("Direct download link detected"))
                else:
                    self.log_info(_("Direct download link not found"))

            if not self.link and not self.last_download:
                self.preload()

                if self.info.get('status', 3) is not 2:
                    self.grab_info()

                if self.premium and (not self.CHECK_TRAFFIC or self.check_traffic()):
                    self.log_info(_("Processing as premium download..."))
                    self.handle_premium(pyfile)

                elif not self.LOGIN_ACCOUNT or (not self.CHECK_TRAFFIC or self.check_traffic()):
                    self.log_info(_("Processing as free download..."))
                    self.handle_free(pyfile)

        if not self.last_download:
            self.log_info(_("Downloading file..."))
            self.download(self.link, disposition=self.DISPOSITION)


    def check_download(self):
        super(SimpleHoster, self).check_download()

        self.log_info(_("Checking downloaded file with built-in rules...")
        for r, p in self.FILE_ERRORS:
            errmsg = self.check_file({r: re.compile(p)})
            if errmsg is not None:
                errmsg = errmsg.strip().capitalize()

                try:
                    errmsg += " | " + self.last_check.group(1).strip()

                except Exception:
                    pass

                self.log_warning(_("Check result: ") + errmsg, _("Waiting 1 minute and retry"))
                self.wait(60, reconnect=True)
                self.restart(errmsg)
        else:
            if self.CHECK_FILE:
                self.log_info(_("Checking downloaded file with custom rules...")

                with open(encode(self.last_download), "rb") as f:
                    self.data = f.read(1048576)  #@TODO: Recheck in 0.4.10

                self.check_errors()

        self.log_info(_("File is OK"))


    def check_errors(self):
        if not self.data:
            self.log_debug("No data to check")
            return

        if self.IP_BLOCKED_PATTERN and re.search(self.IP_BLOCKED_PATTERN, self.data):
            self.fail(_("Connection from your current IP address is not allowed"))

        elif not self.premium:
            if self.PREMIUM_ONLY_PATTERN and re.search(self.PREMIUM_ONLY_PATTERN, self.data):
                self.fail(_("File can be downloaded by premium users only"))

            elif self.SIZE_LIMIT_PATTERN and re.search(self.SIZE_LIMIT_PATTERN, self.data):
                self.fail(_("File too large for free download"))

            elif self.DL_LIMIT_PATTERN and re.search(self.DL_LIMIT_PATTERN, self.data):
                m = re.search(self.DL_LIMIT_PATTERN, self.data)
                try:
                    errmsg = m.group(1)

                except (AttributeError, IndexError):
                    errmsg = m.group(0)

                finally:
                    errmsg = re.sub(r'<.*?>', " ", errmsg.strip())

                self.info['error'] = errmsg
                self.log_warning(errmsg)

                wait_time = parse_time(errmsg)
                self.wait(wait_time, reconnect=wait_time > self.get_config("max_wait", 10) * 60)
                self.restart(_("Download limit exceeded"))

        if self.HAPPY_HOUR_PATTERN and re.search(self.HAPPY_HOUR_PATTERN, self.data):
            self.multiDL = True

        if self.ERROR_PATTERN:
            m = re.search(self.ERROR_PATTERN, self.data)
            if m is not None:
                try:
                    errmsg = m.group(1).strip()

                except (AttributeError, IndexError):
                    errmsg = m.group(0).strip()

                finally:
                    errmsg = re.sub(r'<.*?>', " ", errmsg)

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
                    self.fail(_("File too large for free download"))

                elif re.search('offline|delet|remov|not? (found|(longer)? available)', errmsg, re.I):
                    self.offline()

                elif re.search('filename', errmsg, re.I):
                    self.fail(_("Invalid url"))

                elif re.search('premium', errmsg, re.I):
                    self.fail(_("File can be downloaded by premium users only"))

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


    #: Deprecated method (Remove in 0.4.10)
    def get_fileInfo(self):
        self.info.clear()
        self.grab_info()
        return self.info


    def handle_direct(self, pyfile):
        self.link = self.isdownload(pyfile.url)


    def handle_multi(self, pyfile):  #: Multi-hoster handler
        pass


    def handle_free(self, pyfile):
        if not self.LINK_FREE_PATTERN:
            self.log_warning(_("Free download not implemented"))

        m = re.search(self.LINK_FREE_PATTERN, self.data)
        if m is None:
            self.error(_("Free download link not found"))
        else:
            self.link = m.group(1)


    def handle_premium(self, pyfile):
        if not self.LINK_PREMIUM_PATTERN:
            self.log_warning(_("Premium download not implemented"))
            self.restart(premium=False)

        m = re.search(self.LINK_PREMIUM_PATTERN, self.data)
        if m is None:
            self.error(_("Premium download link not found"))
        else:
            self.link = m.group(1)
