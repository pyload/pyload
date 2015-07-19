# -*- coding: utf-8 -*-

from __future__ import with_statement

import datetime
import mimetypes
import os
import re
import time
import urlparse

from module.PyFile import statusMap as _statusMap
from module.network.HTTPRequest import BadHeader
from module.network.RequestFactory import getURL as get_url
from module.plugins.internal.Hoster import Hoster, create_getInfo, parse_fileInfo
from module.plugins.internal.Plugin import Fail, Retry, fixurl, replace_patterns, set_cookies
from module.utils import fixup, fs_encode, parseFileSize as parse_size


#@TODO: Adapt and move to PyFile in 0.4.10
statusMap = dict((v, k) for k, v in _statusMap.iteritems())


class SimpleHoster(Hoster):
    __name__    = "SimpleHoster"
    __type__    = "hoster"
    __version__ = "1.71"
    __status__  = "stable"

    __pattern__ = r'^unmatchable$'
    __config__  = [("use_premium", "bool", "Use premium account if available"          , True),
                   ("fallback"   , "bool", "Fallback to free download if premium fails", True)]

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
    NAME_REPLACEMENTS = [("&#?\w+;", fixup)]
    SIZE_REPLACEMENTS = []
    URL_REPLACEMENTS  = []

    FILE_ERRORS = [('Html error'   , r'\A(?:\s*<.+>)?((?:[\w\s]*(?:[Ee]rror|ERROR)\s*\:?)?\s*\d{3})(?:\Z|\s+)'),
                   ('Request error', r'([Aa]n error occured while processing your request)'                   ),
                   ('Html file'    , r'\A\s*<!DOCTYPE html'                                                   )]

    CHECK_FILE    = True   #: Set to False to not check the last downloaded file with declared error patterns
    CHECK_TRAFFIC = False  #: Set to True to force checking traffic left for premium account
    COOKIES       = True   #: or False or list of tuples [(domain, name, value)]
    DIRECT_LINK   = None   #: Set to True to looking for direct link (as defined in handle_direct method), set to None to do it if self.account is True else False
    DISPOSITION   = True   #: Set to True to use any content-disposition value in http header as file name
    LOGIN_ACCOUNT = False  #: Set to True to require account login
    LOGIN_PREMIUM = False  #: Set to True to require premium account login
    MULTI_HOSTER  = False  #: Set to True to leech other hoster link (as defined in handle_multi method)
    TEXT_ENCODING = True   #: Set to encoding name if encoding value in http header is not correct

    LINK_PATTERN = None


    @classmethod
    def api_info(cls, url):
        return super(SimpleHoster, self).get_info(url)


    @classmethod
    def get_info(cls, url="", html=""):
        info   = cls.api_info(url)
        online = True if info['status'] is 2 else False

        try:
            info['pattern'] = re.match(cls.__pattern__, url).groupdict()  #: Pattern groups will be saved here

        except Exception:
            info['pattern'] = {}

        if not html and not online:
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
            if hasattr(cls, "OFFLINE_PATTERN") and re.search(cls.OFFLINE_PATTERN, html):
                info['status'] = 1

            elif hasattr(cls, "TEMP_OFFLINE_PATTERN") and re.search(cls.TEMP_OFFLINE_PATTERN, html):
                info['status'] = 6

            else:
                for pattern in ("INFO_PATTERN", "NAME_PATTERN", "SIZE_PATTERN", "HASHSUM_PATTERN"):
                    try:
                        attr  = getattr(cls, pattern)
                        pdict = re.search(attr, html).groupdict()

                        if all(True for k in pdict if k not in info['pattern']):
                            info['pattern'].update(pdict)

                    except AttributeError:
                        continue

                    else:
                        online = True

        if online:
            info['status'] = 2

            if 'N' in info['pattern']:
                info['name'] = replace_patterns(fixurl(info['pattern']['N']),
                                                cls.NAME_REPLACEMENTS)

            if 'S' in info['pattern']:
                size = replace_patterns(info['pattern']['S'] + info['pattern']['U'] if 'U' in info['pattern'] else info['pattern']['S'],
                                        cls.SIZE_REPLACEMENTS)
                info['size'] = parse_size(size)

            elif isinstance(info['size'], basestring):
                unit = info['units'] if 'units' in info else None
                info['size'] = parse_size(info['size'], unit)

            if 'H' in info['pattern']:
                hashtype = info['pattern']['T'] if 'T' in info['pattern'] else "hash"
                info[hashtype] = info['pattern']['H']

        if not info['pattern']:
            info.pop('pattern', None)

        return info


    def setup(self):
        self.resume_download = self.multi_dl = self.premium


    def prepare(self):
        self.pyfile.error = ""  #@TODO: Remove in 0.4.10

        self.html      = ""  #@TODO: Recheck in 0.4.10
        self.link      = ""  #@TODO: Recheck in 0.4.10
        self.direct_dl = False
        self.multihost = False

        if not self.get_config('use_premium', True):
            self.retry_free()

        if self.LOGIN_PREMIUM and not self.premium:
            self.fail(_("Required premium account not found"))

        if self.LOGIN_ACCOUNT and not self.account:
            self.fail(_("Required account not found"))

        self.req.setOption("timeout", 120)

        if isinstance(self.COOKIES, list):
            set_cookies(self.req.cj, self.COOKIES)

        if self.LINK_PATTERN:
            if not hasattr(self, 'LINK_FREE_PATTERN'):
                self.LINK_FREE_PATTERN = self.LINK_PATTERN

            if not hasattr(self, 'LINK_PREMIUM_PATTERN'):
                self.LINK_PREMIUM_PATTERN = self.LINK_PATTERN

        if (self.MULTI_HOSTER
            and (self.__pattern__ != self.pyload.pluginManager.hosterPlugins[self.__name__]['pattern']
                 or re.match(self.__pattern__, self.pyfile.url) is None)):
            self.multihost = True
            return

        if self.DIRECT_LINK is None:
            self.direct_dl = bool(self.account)
        else:
            self.direct_dl = self.DIRECT_LINK

        self.pyfile.url = replace_patterns(self.pyfile.url, self.URL_REPLACEMENTS)


    def preload(self):
        self.html = self.load(self.pyfile.url,
                              cookies=bool(self.COOKIES),
                              ref=False,
                              decode=self.TEXT_ENCODING)


    def process(self, pyfile):
        try:
            self.prepare()
            self.check_info()

            if self.direct_dl:
                self.log_debug("Looking for direct download link...")
                self.handle_direct(pyfile)

            if self.multihost and not self.link and not self.last_download:
                self.log_debug("Looking for leeched download link...")
                self.handle_multi(pyfile)

                if not self.link and not self.last_download:
                    self.MULTI_HOSTER = False
                    self.retry(1, reason=_("Multi hoster fails"))

            if not self.link and not self.last_download:
                self.preload()
                self.check_info()

                if self.premium and (not self.CHECK_TRAFFIC or self.check_traffic_left()):
                    self.log_debug("Handled as premium download")
                    self.handle_premium(pyfile)

                elif not self.LOGIN_ACCOUNT or (not self.CHECK_TRAFFIC or self.check_traffic_left()):
                    self.log_debug("Handled as free download")
                    self.handle_free(pyfile)

            self.download(self.link, ref=False, disposition=self.DISPOSITION)
            self.check_file()

        except Fail, e:  #@TODO: Move to PluginThread in 0.4.10
            err = str(e)  #@TODO: Recheck in 0.4.10

            if err == _("No captcha result obtained in appropiate time by any of the plugins."):  #@TODO: Fix in 0.4.10
                self.check_file()

            elif self.get_config('fallback', True) and self.premium:
                self.log_warning(_("Premium download failed"), e)
                self.retry_free()

            else:
                raise Fail(err)


    def check_file(self):
        lastDownload = fs_encode(self.last_download)

        if self.c_task and not self.last_download:
            self.invalid_captcha()
            self.retry(10, reason=_("Wrong captcha"))

        elif self.check_download({'Empty file': re.compile(r'\A((.|)(\2|\s)*)\Z')},
                                 file_size=self.info['size']):
            self.error(_("Empty file"))

        else:
            self.log_debug("Checking last downloaded file with built-in rules")
            for r, p in self.FILE_ERRORS:
                errmsg = self.check_download({r: re.compile(p)})
                if errmsg is not None:
                    errmsg = errmsg.strip().capitalize()

                    try:
                        errmsg += " | " + self.last_check.group(1).strip()
                    except Exception:
                        pass

                    self.log_warning(_("Check result: ") + errmsg, _("Waiting 1 minute and retry"))
                    self.want_reconnect = True
                    self.retry(wait_time=60, reason=errmsg)
            else:
                if self.CHECK_FILE:
                    self.log_debug("Checking last downloaded file with custom rules")
                    with open(lastDownload, "rb") as f:
                        self.html = f.read(50000)  #@TODO: Recheck in 0.4.10
                    self.check_errors()

        self.log_debug("No file errors found")


    def check_errors(self):
        if not self.html:
            self.log_warning(_("No html code to check"))
            return

        if hasattr(self, 'IP_BLOCKED_PATTERN') and re.search(self.IP_BLOCKED_PATTERN, self.html):
            self.fail(_("Connection from your current IP address is not allowed"))

        elif not self.premium:
            if hasattr(self, 'PREMIUM_ONLY_PATTERN') and re.search(self.PREMIUM_ONLY_PATTERN, self.html):
                self.fail(_("File can be downloaded by premium users only"))

            elif hasattr(self, 'SIZE_LIMIT_PATTERN') and re.search(self.SIZE_LIMIT_PATTERN, self.html):
                self.fail(_("File too large for free download"))

            elif hasattr(self, 'DL_LIMIT_PATTERN') and re.search(self.DL_LIMIT_PATTERN, self.html):
                m = re.search(self.DL_LIMIT_PATTERN, self.html)
                try:
                    errmsg = m.group(1).strip()
                except Exception:
                    errmsg = m.group(0).strip()

                self.info['error'] = re.sub(r'<.*?>', " ", errmsg)
                self.log_warning(self.info['error'])

                if re.search('da(il)?y|today', errmsg, re.I):
                    wait_time = seconds_to_midnight(gmt=2)
                else:
                    wait_time = sum(int(v) * {'hr': 3600, 'hour': 3600, 'min': 60, 'sec': 1, "": 1}[u.lower()] for v, u in
                                re.findall(r'(\d+)\s*(hr|hour|min|sec|)', errmsg, re.I))

                self.want_reconnect = wait_time > 300
                self.retry(1, wait_time, _("Download limit exceeded"))

        if hasattr(self, 'HAPPY_HOUR_PATTERN') and re.search(self.HAPPY_HOUR_PATTERN, self.html):
            self.multi_dl = True

        if hasattr(self, 'ERROR_PATTERN'):
            m = re.search(self.ERROR_PATTERN, self.html)
            if m:
                try:
                    errmsg = m.group(1).strip()
                except Exception:
                    errmsg = m.group(0).strip()

                self.info['error'] = re.sub(r'<.*?>', " ", errmsg)
                self.log_warning(self.info['error'])

                if re.search('limit|wait|slot', errmsg, re.I):
                    if re.search("da(il)?y|today", errmsg):
                        wait_time = seconds_to_midnight(gmt=2)
                    else:
                        wait_time = sum(int(v) * {'hr': 3600, 'hour': 3600, 'min': 60, 'sec': 1, "": 1}[u.lower()] for v, u in
                                    re.findall(r'(\d+)\s*(hr|hour|min|sec|)', errmsg, re.I))

                    self.want_reconnect = wait_time > 300
                    self.retry(1, wait_time, _("Download limit exceeded"))

                elif re.search('country|ip|region|nation', errmsg, re.I):
                    self.fail(_("Connection from your current IP address is not allowed"))

                elif re.search('captcha|code', errmsg, re.I):
                    self.invalid_captcha()
                    self.retry(10, reason=_("Wrong captcha"))

                elif re.search('countdown|expired', errmsg, re.I):
                    self.retry(10, 60, _("Link expired"))

                elif re.search('maintenance|maintainance|temp', errmsg, re.I):
                    self.temp_offline()

                elif re.search('up to|size', errmsg, re.I):
                    self.fail(_("File too large for free download"))

                elif re.search('offline|delet|remov|not? (found|(longer)? available)', errmsg, re.I):
                    self.offline()

                elif re.search('filename', errmsg, re.I):
                    url_p = urlparse.urlparse(self.pyfile.url)
                    self.pyfile.url = "%s://%s/%s" % (url_p.scheme, url_p.netloc, url_p.path.strip('/').split('/')[0])
                    self.retry(1, reason=_("Wrong url"))

                elif re.search('premium', errmsg, re.I):
                    self.fail(_("File can be downloaded by premium users only"))

                else:
                    self.want_reconnect = True
                    self.retry(wait_time=60, reason=errmsg)

        elif hasattr(self, 'WAIT_PATTERN'):
            m = re.search(self.WAIT_PATTERN, self.html)
            if m:
                try:
                    waitmsg = m.group(1).strip()
                except Exception:
                    waitmsg = m.group(0).strip()

                wait_time = sum(int(v) * {'hr': 3600, 'hour': 3600, 'min': 60, 'sec': 1, "": 1}[u.lower()] for v, u in
                                re.findall(r'(\d+)\s*(hr|hour|min|sec|)', waitmsg, re.I))
                self.wait(wait_time, wait_time > 300)

        self.info.pop('error', None)


    def check_status(self, getinfo=True):
        if not self.info or getinfo:
            self.log_debug("Update file info...")
            self.log_debug("Previous file info: %s" % self.info)
            self.info.update(self.get_info(self.pyfile.url, self.html))
            self.log_debug("Current file info: %s"  % self.info)

        try:
            status = self.info['status']

            if status is 1:
                self.offline()

            elif status is 6:
                self.temp_offline()

            elif status is 8:
                self.fail(self.info['error'] if 'error' in self.info else _("Failed"))

        finally:
            self.log_debug("File status: %s" % statusMap[status])


    def check_name_size(self, getinfo=True):
        if not self.info or getinfo:
            self.log_debug("Update file info...")
            self.log_debug("Previous file info: %s" % self.info)
            self.info.update(self.get_info(self.pyfile.url, self.html))
            self.log_debug("Current file info: %s"  % self.info)

        try:
            url  = self.info['url'].strip()
            name = self.info['name'].strip()
            if name and name != url:
                self.pyfile.name = name

        except Exception:
            pass

        try:
            size = self.info['size']
            if size > 0:
                self.pyfile.size = size

        except Exception:
            pass

        self.log_debug("File name: %s" % self.pyfile.name,
                      "File size: %s byte" % self.pyfile.size if self.pyfile.size > 0 else "File size: Unknown")


    def check_info(self):
        self.check_name_size()

        if self.html:
            self.check_errors()
            self.check_name_size()

        self.check_status(getinfo=False)


    #: Deprecated method
    def get_fileInfo(self):
        self.info = {}
        self.check_info()
        return self.info


    def handle_direct(self, pyfile):
        link = self.direct_link(pyfile.url, self.resume_download)

        if link:
            self.log_info(_("Direct download link detected"))
            self.link = link
        else:
            self.log_debug("Direct download link not found")


    def handle_multi(self, pyfile):  #: Multi-hoster handler
        pass


    def handle_free(self, pyfile):
        if not hasattr(self, 'LINK_FREE_PATTERN'):
            self.log_error(_("Free download not implemented"))

        m = re.search(self.LINK_FREE_PATTERN, self.html)
        if m is None:
            self.error(_("Free download link not found"))
        else:
            self.link = m.group(1)


    def handle_premium(self, pyfile):
        if not hasattr(self, 'LINK_PREMIUM_PATTERN'):
            self.log_error(_("Premium download not implemented"))
            self.log_debug("Handled as free download")
            self.handle_free(pyfile)

        m = re.search(self.LINK_PREMIUM_PATTERN, self.html)
        if m is None:
            self.error(_("Premium download link not found"))
        else:
            self.link = m.group(1)


    def retry_free(self):
        if not self.premium:
            return
        self.premium = False
        self.account = None
        self.req = self.pyload.requestFactory.getRequest(self.__name__)
        raise Retry(_("Fallback to free download"))
