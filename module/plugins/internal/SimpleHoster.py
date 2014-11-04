# -*- coding: utf-8 -*-

import re

from time import time
from urlparse import urlparse

from pycurl import FOLLOWLOCATION

from module.network.CookieJar import CookieJar
from module.network.RequestFactory import getURL
from module.plugins.Hoster import Hoster
from module.plugins.Plugin import Fail
from module.utils import fixup, html_unescape, parseFileSize


#@TODO: Remove in 0.4.10 and redirect to self.error instead
def _error(self, reason, type):
        if not reason and not type:
            type = "unknown"

        msg  = _("%s error") % type.strip().capitalize() if type else _("Error")
        msg += ": " + reason.strip() if reason else ""
        msg += _(" | Plugin may be out of date")

        raise Fail(msg)


#@TODO: Remove in 0.4.10
def _wait(self, seconds, reconnect):
    if seconds:
        self.setWait(seconds, reconnect)
    super(SimpleHoster, self).wait()


def replace_patterns(string, ruleslist):
    for r in ruleslist:
        rf, rt = r
        string = re.sub(rf, rt, string)
    return string


def set_cookies(cj, cookies):
    for cookie in cookies:
        if isinstance(cookie, tuple) and len(cookie) == 3:
            domain, name, value = cookie
            cj.setCookie(domain, name, value)


def parseHtmlTagAttrValue(attr_name, tag):
    m = re.search(r"%s\s*=\s*([\"']?)((?<=\")[^\"]+|(?<=')[^']+|[^>\s\"'][^>\s]*)\1" % attr_name, tag, re.I)
    return m.group(2) if m else None


def parseHtmlForm(attr_str, html, input_names=None):
    for form in re.finditer(r"(?P<tag><form[^>]*%s[^>]*>)(?P<content>.*?)</?(form|body|html)[^>]*>" % attr_str,
                            html, re.S | re.I):
        inputs = {}
        action = parseHtmlTagAttrValue("action", form.group('tag'))
        for inputtag in re.finditer(r'(<(input|textarea)[^>]*>)([^<]*(?=</\2)|)', form.group('content'), re.S | re.I):
            name = parseHtmlTagAttrValue("name", inputtag.group(1))
            if name:
                value = parseHtmlTagAttrValue("value", inputtag.group(1))
                if not value:
                    inputs[name] = inputtag.group(3) or ''
                else:
                    inputs[name] = value

        if isinstance(input_names, dict):
            # check input attributes
            for key, val in input_names.iteritems():
                if key in inputs:
                    if isinstance(val, basestring) and inputs[key] == val:
                        continue
                    elif isinstance(val, tuple) and inputs[key] in val:
                        continue
                    elif hasattr(val, "search") and re.match(val, inputs[key]):
                        continue
                    break  # attibute value does not match
                else:
                    break  # attibute name does not match
            else:
                return action, inputs  # passed attribute check
        else:
            # no attribute check
            return action, inputs

    return {}, None  # no matching form found


def parseFileInfo(self, url="", html=""):
    if not url and hasattr(self, "pyfile"):
        url = self.pyfile.url

    info = {'name': url, 'size': 0, 'status': 3}

    if not html:
        if url:
            return create_getInfo(self)([url]).next()

        elif hasattr(self, "req") and self.req.http.code == '404':
            info['status'] = 1

        elif hasattr(self, "html"):
            html = self.html

    if html:
        if hasattr(self, "OFFLINE_PATTERN") and re.search(self.OFFLINE_PATTERN, html):
            info['status'] = 1

        elif hasattr(self, "FILE_OFFLINE_PATTERN") and re.search(self.FILE_OFFLINE_PATTERN, html):  #@TODO: Remove in 0.4.10
            info['status'] = 1

        elif hasattr(self, "TEMP_OFFLINE_PATTERN") and re.search(self.TEMP_OFFLINE_PATTERN, html):
            info['status'] = 6

        else:
            online = False
            try:
                info.update(re.match(self.__pattern__, url).groupdict())
            except:
                pass

            for pattern in ("INFO_PATTERN", "NAME_PATTERN", "SIZE_PATTERN",
                            "FILE_INFO_PATTERN", "FILE_NAME_PATTERN", "FILE_SIZE_PATTERN"):  #@TODO: Remove in 0.4.10
                try:
                    info.update(re.search(getattr(self, pattern), html).groupdict())
                    online = True
                except AttributeError:
                    continue

            if online:
                # File online, return name and size
                info['status'] = 2

                if 'N' in info:
                    info['name'] = replace_patterns(info['N'].strip(),
                                                    self.FILE_NAME_REPLACEMENTS if hasattr(self, "FILE_NAME_REPLACEMENTS") else self.NAME_REPLACEMENTS)  #@TODO: Remove FILE_NAME_REPLACEMENTS check in 0.4.10

                if 'S' in info:
                    size = replace_patterns(info['S'] + info['U'] if 'U' in info else info['S'],
                                            self.FILE_SIZE_REPLACEMENTS if hasattr(self, "FILE_SIZE_REPLACEMENTS") else self.SIZE_REPLACEMENTS)  #@TODO: Remove FILE_SIZE_REPLACEMENTS check in 0.4.10
                    info['size'] = parseFileSize(size)

                elif isinstance(info['size'], basestring):
                    unit = info['units'] if 'units' in info else None
                    info['size'] = parseFileSize(info['size'], unit)

    if hasattr(self, "html") and self.html is None:
        self.html = html

    if hasattr(self, "info"):
        try:
            self.logDebug(_("File info (before update): %s") % self.info)
        except:
            pass

        self.info.update(info)

        try:
            self.logDebug(_("File info (after update): %s") % self.info)
        except:
            pass

    return info['name'], info['size'], info['status'], url


def create_getInfo(plugin):

    def getInfo(urls):
        for url in urls:
            if hasattr(plugin, "COOKIES") and isinstance(plugin.COOKIES, list):
                cj = CookieJar(plugin.__name__)
                set_cookies(cj, plugin.COOKIES)
            else:
                cj = None

            if hasattr(plugin, "URL_REPLACEMENTS"):
                url = replace_patterns(url, plugin.URL_REPLACEMENTS)

            elif hasattr(plugin, "FILE_URL_REPLACEMENTS"):  #@TODO: Remove in 0.4.10
                url = replace_patterns(url, plugin.FILE_URL_REPLACEMENTS)

            if hasattr(plugin, "TEXT_ENCODING"):
                html = getURL(url, cookies=bool(cj), decode=not plugin.TEXT_ENCODING)
                if isinstance(plugin.TEXT_ENCODING, basestring):
                    html = unicode(html, plugin.TEXT_ENCODING)
            else:
                html = getURL(url, cookies=bool(cj), decode=True)

            yield parseFileInfo(plugin, url, html)

    return getInfo


def timestamp():
    return int(time() * 1000)


class SimpleHoster(Hoster):
    __name__    = "SimpleHoster"
    __type__    = "hoster"
    __version__ = "0.50"

    __pattern__ = r'^unmatchable$'

    __description__ = """Simple hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("stickell", "l.stickell@yahoo.it"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    """
    Following patterns should be defined by each hoster:

      INFO_PATTERN: (optional) Name and Size of the file
        example: INFO_PATTERN = r'(?P<N>file_name) (?P<S>file_size) (?P<U>size_unit)'
      or
        NAME_PATTERN: (optional) Name that will be set for the file
          example: NAME_PATTERN = r'(?P<N>file_name)'
        SIZE_PATTERN: (optional) Size that will be checked for the file
          example: SIZE_PATTERN = r'(?P<S>file_size) (?P<U>size_unit)'

      OFFLINE_PATTERN: (optional) Checks if the file is yet available online
        example: OFFLINE_PATTERN = r'File (deleted|not found)'

      TEMP_OFFLINE_PATTERN: (optional) Checks if the file is temporarily offline
        example: TEMP_OFFLINE_PATTERN = r'Server (maintenance|maintainance)'

      PREMIUM_ONLY_PATTERN: (optional) Checks if the file can be downloaded only with a premium account
        example: PREMIUM_ONLY_PATTERN = r'Premium account required'


    Instead overriding handleFree and handlePremium methods now you can define patterns for direct download:

      LINK_FREE_PATTERN: (optional) group(1) should be the direct link for free download
        example: LINK_FREE_PATTERN = r'<div class="link"><a href="(.+?)"'

      LINK_PREMIUM_PATTERN: (optional) group(1) should be the direct link for premium download
        example: LINK_PREMIUM_PATTERN = r'<div class="link"><a href="(.+?)"'
    """

    NAME_REPLACEMENTS = [("&#?\w+;", fixup)]
    SIZE_REPLACEMENTS = []
    URL_REPLACEMENTS  = []

    TEXT_ENCODING       = False  #: Set to True or encoding name if encoding in http header is not correct
    COOKIES             = True  #: or False or list of tuples [(domain, name, value)]
    FORCE_CHECK_TRAFFIC = False  #: Set to True to force checking traffic left for premium account


    def init(self):
        self.info = {}


    def setup(self):
        self.resumeDownload = self.multiDL = self.premium


    def prepare(self):
        if isinstance(self.COOKIES, list):
            set_cookies(self.req.cj, self.COOKIES)

        self.req.setOption("timeout", 120)

        self.pyfile.url = replace_patterns(self.pyfile.url,
                                           self.FILE_URL_REPLACEMENTS if hasattr(self, "FILE_URL_REPLACEMENTS") else self.URL_REPLACEMENTS)  #@TODO: Remove FILE_URL_REPLACEMENTS check in 0.4.10

        if self.premium:
            self.logDebug(_("Checking for direct download link..."))
            direct_link = self.getDirectLink(self.pyfile.url)
            if direct_link:
                return direct_link
            else:
                self.logDebug(_("No direct download link found"))
                self.html = None
                self.info = {}

        if self.html is None:
            self.html = self.load(self.pyfile.url, decode=not self.TEXT_ENCODING, cookies=bool(self.COOKIES))

        if isinstance(self.TEXT_ENCODING, basestring):
            self.html = unicode(self.html, self.TEXT_ENCODING)


    def process(self, pyfile):
        direct_link = self.prepare()

        if isinstance(direct_link, basestring):
            self.logInfo(_("Direct download link detected"))
            self.download(direct_link, ref=True, cookies=True, disposition=True)

        elif self.html is None:
            self.fail(_("No html retrieved"))

        else:
            premium_only = hasattr(self, 'PREMIUM_ONLY_PATTERN') and re.search(self.PREMIUM_ONLY_PATTERN, self.html)
            if not premium_only and not self.info:  #: Usually premium only pages doesn't show any file information
                self.getFileInfo()

            if self.premium and (not self.FORCE_CHECK_TRAFFIC or self.checkTrafficLeft()):
                self.logDebug("Handled as premium download")
                self.handlePremium()
            elif premium_only:
                self.fail(_("Link require a premium account to be handled"))
            else:
                self.logDebug("Handled as free download")
                self.handleFree()


    def getDirectLink(self, url):
        self.req.http.c.setopt(FOLLOWLOCATION, 0)

        html = self.load(url, ref=True, decode=True)

        self.req.http.c.setopt(FOLLOWLOCATION, 1)

        if parseFileInfo(self, url, html)[2] is not 2:
            try:
                return re.search(r"Location\s*:\s*(.+)", self.req.http.header, re.I).group(1)
            except:
                pass


    def getFileInfo(self):
        name, size, status, url = parseFileInfo(self)

        if name and name != url:
            self.pyfile.name = name
        else:
            self.pyfile.name = self.info['name'] = html_unescape(urlparse(url).path.split("/")[-1])

        if status is 1:
            self.offline()

        elif status is 6:
            self.tempOffline()

        elif status is not 2:
            self.error(_("File info: %s") % self.info)

        if size:
            self.pyfile.size = size
        else:
            self.logError(_("File size not parsed"))

        self.logDebug("FILE NAME: %s" % self.pyfile.name, "FILE SIZE: %d" % self.pyfile.size or _("Unknown"))
        return self.info


    def handleFree(self):
        if not hasattr(self, 'LINK_FREE_PATTERN'):
            self.fail(_("Free download not implemented"))

        try:
            m = re.search(self.LINK_FREE_PATTERN, self.html)
            if m is None:
                self.error(_("Free download link not found"))

            link = m.group(1)
        except Exception, e:
            self.fail(str(e))
        else:
            self.download(link, ref=True, cookies=True, disposition=True)


    def handlePremium(self):
        if not hasattr(self, 'LINK_PREMIUM_PATTERN'):
            self.fail(_("Premium download not implemented"))

        try:
            m = re.search(self.LINK_PREMIUM_PATTERN, self.html)
            if m is None:
                self.error(_("Premium download link not found"))

            link = m.group(1)
        except Exception, e:
            self.fail(str(e))
        else:
            self.download(link, ref=True, cookies=True, disposition=True)


    def longWait(self, wait_time=None, max_tries=3):
        if wait_time and isinstance(wait_time, (int, long, float)):
            time_str = "%dh %dm" % divmod(wait_time / 60, 60)
        else:
            wait_time = 900
            time_str = _("(unknown time)")
            max_tries = 100

        self.logInfo(_("Download limit reached, reconnect or wait %s") % time_str)

        self.setWait(wait_time, True)
        self.wait()
        self.retry(max_tries=max_tries, reason=_("Download limit reached"))


    def parseHtmlForm(self, attr_str='', input_names=None):
        return parseHtmlForm(attr_str, self.html, input_names)


    def checkTrafficLeft(self):
        traffic = self.account.getAccountInfo(self.user, True)['trafficleft']

        if traffic is None:
            return False
        elif traffic == -1:
            return True
        else:
            size = self.pyfile.size / 1024
            self.logInfo(_("Filesize: %i KiB, Traffic left for user %s: %i KiB") % (size, self.user, traffic))
            return size <= traffic


    #@TODO: Remove in 0.4.10
    def wait(self, seconds=0, reconnect=None):
        return _wait(self, seconds, reconnect)


    def error(self, reason="", type="parse"):
        return _error(self, reason, type)
