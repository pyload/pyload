# -*- coding: utf-8 -*-

from __future__ import with_statement

import mimetypes
import os
import re
import time
import urlparse

from module.PyFile import statusMap as _statusMap
from module.network.HTTPRequest import BadHeader
from module.network.RequestFactory import getURL as get_url
from module.plugins.internal.Hoster import Hoster, create_getInfo, parse_fileInfo
from module.plugins.internal.Plugin import Fail, encode, fixurl, replace_patterns, seconds_to_midnight, set_cookie, set_cookies
from module.utils import fixup, fs_encode, parseFileSize as parse_size


#@TODO: Adapt and move to PyFile in 0.4.10
statusMap = dict((v, k) for k, v in _statusMap.items())


class SimpleHoster(Hoster):
    __name__    = "SimpleHoster"
    __type__    = "hoster"
    __version__ = "1.78"
    __status__  = "testing"

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
    CHECK_TRAFFIC = False  #: Set to True to reload checking traffic left for premium account
    COOKIES       = True   #: or False or list of tuples [(domain, name, value)]
    DIRECT_LINK   = None   #: Set to True to looking for direct link (as defined in handle_direct method), set to None to do it if self.account is True else False
    DISPOSITION   = True   #: Set to True to use any content-disposition value in http header as file name
    LOGIN_ACCOUNT = False  #: Set to True to require account login
    LOGIN_PREMIUM = False  #: Set to True to require premium account login
    LEECH_HOSTER  = False  #: Set to True to leech other hoster link (as defined in handle_multi method)
    TEXT_ENCODING = True   #: Set to encoding name if encoding value in http header is not correct

    LINK_PATTERN = None


    @classmethod
    def api_info(cls, url):
        return super(SimpleHoster, cls).get_info(url)


    @classmethod
    def get_info(cls, url="", html=""):
        info   = cls.api_info(url)
        online = True if info['status'] == 2 else False

        try:
            info['pattern'] = re.match(cls.__pattern__, url).groupdict()  #: Pattern groups will be saved here

        except Exception:
            info['pattern'] = {}

        if not html and not online:
            if not url:
                info['error']  = "missing url"
                info['status'] = 1

            elif info['status'] == 3:
                try:
                    html = get_url(url, cookies=cls.COOKIES, decode=cls.TEXT_ENCODING)

                except BadHeader, e:
                    info['error'] = "%d: %s" % (e.code, e.content)

                    if e.code == 404:
                        info['status'] = 1

                    elif e.code == 503:
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
        self.resume_download = self.multiDL = self.premium


    def prepare(self):
        self.pyfile.error  = ""  #@TODO: Remove in 0.4.10
        self.html          = ""  #@TODO: Recheck in 0.4.10
        self.link          = ""  #@TODO: Recheck in 0.4.10
        self.last_download = ""
        self.direct_dl     = False
        self.leech_dl      = False

        if not self.get_config('use_premium', True):
            self.restart(nopremium=True)

        if self.LOGIN_PREMIUM and not self.premium:
            self.fail(_("Required premium account not found"))
            self.LOGIN_ACCOUNT = True

        if self.LOGIN_ACCOUNT and not self.account:
            self.fail(_("Required account not found"))

        self.req.setOption("timeout", 120)

        if hasattr(self, 'COOKIES') and isinstance(self.COOKIES, list):
            set_cookies(self.req.cj, self.COOKIES)

        if self.LINK_PATTERN:
            if not hasattr(self, 'LINK_FREE_PATTERN'):
                self.LINK_FREE_PATTERN = self.LINK_PATTERN

            if not hasattr(self, 'LINK_PREMIUM_PATTERN'):
                self.LINK_PREMIUM_PATTERN = self.LINK_PATTERN

        if (self.LEECH_HOSTER
            and (self.__pattern__ is not self.pyload.pluginManager.hosterPlugins[self.__name__]['pattern']
                 and re.match(self.__pattern__, self.pyfile.url) is None)):
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
        self.html = self.load(self.pyfile.url,
                              cookies=bool(self.COOKIES),
                              ref=False,
                              decode=self.TEXT_ENCODING)


    def process(self, pyfile):
        try:
            self.prepare()
            self.check_info()  #@TODO: Remove in 0.4.10

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

                    if 'status' not in self.info or self.info['status'] is 3:  #@TODO: Recheck in 0.4.10
                        self.check_info()

                    if self.premium and (not self.CHECK_TRAFFIC or self.check_traffic_left()):
                        self.log_info(_("Processing as premium download..."))
                        self.handle_premium(pyfile)

                    elif not self.LOGIN_ACCOUNT or (not self.CHECK_TRAFFIC or self.check_traffic_left()):
                        self.log_info(_("Processing as free download..."))
                        self.handle_free(pyfile)

            if not self.last_download:
                self.log_info(_("Downloading file..."))
                self.download(self.link, disposition=self.DISPOSITION)

            self.check_file()

        except Fail, e:  #@TODO: Move to PluginThread in 0.4.10
            if self.get_config('fallback', True) and self.premium:
                self.log_warning(_("Premium download failed"), e)
                self.restart(nopremium=True)

            else:
                raise Fail(encode(e))  #@TODO: Remove `encode` in 0.4.10


    def check_file(self):
        self.log_info(_("Checking file..."))

        if self.captcha.task and not self.last_download:
            self.captcha.invalid()
            self.retry(10, reason=_("Wrong captcha"))

        elif self.check_download({'Empty file': re.compile(r'\A((.|)(\2|\s)*)\Z')},
                                 file_size=self.info['size'] if 'size' in self.info else 0,
                                 size_tolerance=1048576,
                                 delete=True):
            self.error(_("Empty file"))

        else:
            self.log_debug("Using default check rules...")
            for r, p in self.FILE_ERRORS:
                errmsg = self.check_download({r: re.compile(p)})
                if errmsg is not None:
                    errmsg = errmsg.strip().capitalize()

                    try:
                        errmsg += " | " + self.last_check.group(1).strip()
                    except Exception:
                        pass

                    self.log_warning(_("Check result: ") + errmsg, _("Waiting 1 minute and retry"))
                    self.wantReconnect = True
                    self.retry(wait_time=60, reason=errmsg)
            else:
                if self.CHECK_FILE:
                    self.log_debug("Using custom check rules...")
                    with open(fs_encode(self.last_download), "rb") as f:
                        self.html = f.read(1048576)  #@TODO: Recheck in 0.4.10
                    self.check_errors()

        self.log_info(_("No errors found"))
        self.pyfile.error = ""


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

                self.wantReconnect = wait_time > 300
                self.retry(1, wait_time, _("Download limit exceeded"))

        if hasattr(self, 'HAPPY_HOUR_PATTERN') and re.search(self.HAPPY_HOUR_PATTERN, self.html):
            self.multiDL = True

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

                    self.wantReconnect = wait_time > 300
                    self.retry(1, wait_time, _("Download limit exceeded"))

                elif re.search('country|ip|region|nation', errmsg, re.I):
                    self.fail(_("Connection from your current IP address is not allowed"))

                elif re.search('captcha|code', errmsg, re.I):
                    self.captcha.invalid()
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
                    self.pyfile.url = "%s://%s/%s" % (url_p.scheme, url_p.netloc, url_p.path.split('/')[0])
                    self.retry(1, reason=_("Wrong url"))

                elif re.search('premium', errmsg, re.I):
                    self.fail(_("File can be downloaded by premium users only"))

                else:
                    self.wantReconnect = True
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
            self.log_info(_("Updating file info..."))
            old_info = self.info.copy()
            self.info.update(self.get_info(self.pyfile.url, self.html))
            self.log_debug("File info: %s" % self.info)
            self.log_debug("Previous file info: %s" % old_info)

        try:
            status = self.info['status'] or None

            if status == 1:
                self.offline()

            elif status == 6:
                self.temp_offline()

            elif status == 8:
                if 'error' in self.info:
                    self.fail(self.info['error'])
                else:
                    self.fail(_("File status: " + statusMap[status]))

        finally:
            self.log_info(_("File status: ") + (statusMap[status] if status else _("Unknown")))


    def check_name_size(self, getinfo=True):
        if not self.info or getinfo:
            self.log_info(_("Updating file info..."))
            old_info = self.info.copy()
            self.info.update(self.get_info(self.pyfile.url, self.html))
            self.log_debug("File info: %s" % self.info)
            self.log_debug("Previous file info: %s" % old_info)

        try:
            url  = self.info['url'].strip()
            name = self.info['name'].strip()

        except KeyError:
            pass

        else:
            if name and name is not url:
                self.pyfile.name = name

        if 'size' in self.info and self.info['size'] > 0:
            self.pyfile.size = int(self.info['size'])  #@TODO: Fix int conversion in 0.4.10

        # self.pyfile.sync()

        name   = self.pyfile.name
        size   = self.pyfile.size
        folder = self.info['folder'] = name

        self.log_info(_("File name: ") + name)
        self.log_info(_("File size: %s bytes") % size if size > 0 else _("File size: Unknown"))
        # self.log_info("File folder: " + folder)


    #@TODO: Rewrite in 0.4.10
    def check_info(self):
        self.check_name_size()

        if self.html:
            self.check_errors()
            self.check_name_size()

        self.check_status(getinfo=False)


    #: Deprecated method (Remove in 0.4.10)
    def get_fileInfo(self):
        self.info = {}
        self.check_info()
        return self.info


    def handle_direct(self, pyfile):
        self.link = self.direct_link(pyfile.url, self.resume_download)


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
            self.log_info(_("Processing as free download..."))
            self.handle_free(pyfile)

        m = re.search(self.LINK_PREMIUM_PATTERN, self.html)
        if m is None:
            self.error(_("Premium download link not found"))
        else:
            self.link = m.group(1)
