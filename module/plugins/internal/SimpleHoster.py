# -*- coding: utf-8 -*-

import re

from time import time
from urllib import unquote
from urlparse import urljoin, urlparse

from module.PyFile import statusMap as _statusMap
from module.network.CookieJar import CookieJar
from module.network.RequestFactory import getURL
from module.plugins.Hoster import Hoster
from module.plugins.Plugin import Fail
from module.utils import fixup, parseFileSize


#@TODO: Adapt and move to PyFile in 0.4.10
statusMap = dict((v, k) for k, v in _statusMap.iteritems())


#@TODO: Remove in 0.4.10 and redirect to self.error instead
def _error(self, reason, type):
        if not reason and not type:
            type = "unknown"

        msg  = _("%s error") % type.strip().capitalize() if type else _("Error")
        msg += ": %s" % reason.strip() if reason else ""
        msg += _(" | Plugin may be out of date")

        raise Fail(msg)


#@TODO: Remove in 0.4.10
def _wait(self, seconds, reconnect):
    if seconds:
        self.setWait(int(seconds) + 1)

    if reconnect is not None:
        self.wantReconnect = reconnect

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


def parseHtmlForm(attr_str, html, input_names={}):
    for form in re.finditer(r"(?P<TAG><form[^>]*%s[^>]*>)(?P<CONTENT>.*?)</?(form|body|html)[^>]*>" % attr_str,
                            html, re.S | re.I):
        inputs = {}
        action = parseHtmlTagAttrValue("action", form.group('TAG'))

        for inputtag in re.finditer(r'(<(input|textarea)[^>]*>)([^<]*(?=</\2)|)', form.group('CONTENT'), re.S | re.I):
            name = parseHtmlTagAttrValue("name", inputtag.group(1))
            if name:
                value = parseHtmlTagAttrValue("value", inputtag.group(1))
                if not value:
                    inputs[name] = inputtag.group(3) or ''
                else:
                    inputs[name] = value

        if input_names:
            # check input attributes
            for key, val in input_names.iteritems():
                if key in inputs:
                    if isinstance(val, basestring) and inputs[key] == val:
                        continue
                    elif isinstance(val, tuple) and inputs[key] in val:
                        continue
                    elif hasattr(val, "search") and re.match(val, inputs[key]):
                        continue
                    break  #: attibute value does not match
                else:
                    break  #: attibute name does not match
            else:
                return action, inputs  #: passed attribute check
        else:
            # no attribute check
            return action, inputs

    return {}, None  #: no matching form found


#: Deprecated
def parseFileInfo(plugin, url="", html=""):
    info = plugin.getInfo(url, html)
    return info['name'], info['size'], info['status'], info['url']


#@TODO: Remove in 0.4.10
#@NOTE: Every plugin must have own parseInfos classmethod to work with 0.4.10
def create_getInfo(plugin):
    return lambda urls: [(info['name'], info['size'], info['status'], info['url']) for info in plugin.parseInfos(urls)]


def timestamp():
    return int(time() * 1000)


#@TODO: Move to hoster class in 0.4.10
def _isDirectLink(self, url, resumable=True):
    header = self.load(url, ref=True, just_header=True, decode=True)

    if not 'location' in header or not header['location']:
        return ""

    location = header['location']

    resumable = False  #@NOTE: Testing...

    if resumable:  #: sometimes http code may be wrong...
        if 'location' in self.load(location, ref=True, cookies=True, just_header=True, decode=True):
            return ""
    else:
        if not 'code' in header or header['code'] != 302:
            return ""

    if urlparse(location).scheme:
        link = location
    else:
        p = urlparse(url)
        base = "%s://%s" % (p.scheme, p.netloc)
        link = urljoin(base, location)

    return link


class SimpleHoster(Hoster):
    __name__    = "SimpleHoster"
    __type__    = "hoster"
    __version__ = "0.72"

    __pattern__ = r'^unmatchable$'

    __description__ = """Simple hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("stickell", "l.stickell@yahoo.it"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    """
    Info patterns should be defined by each hoster:

      INFO_PATTERN: (optional) Name and Size of the file
        example: INFO_PATTERN = r'(?P<N>file_name) (?P<S>file_size) (?P<U>size_unit)'
      or
        NAME_PATTERN: (optional) Name that will be set for the file
          example: NAME_PATTERN = r'(?P<N>file_name)'
        SIZE_PATTERN: (optional) Size that will be checked for the file
          example: SIZE_PATTERN = r'(?P<S>file_size) (?P<U>size_unit)'

      HASHSUM_PATTERN: (optional) Hash code and type of the file
        example: HASHSUM_PATTERN = r'(?P<H>hash_code) (?P<T>MD5)'

      OFFLINE_PATTERN: (optional) Check if the file is yet available online
        example: OFFLINE_PATTERN = r'File (deleted|not found)'

      TEMP_OFFLINE_PATTERN: (optional) Check if the file is temporarily offline
        example: TEMP_OFFLINE_PATTERN = r'Server (maintenance|maintainance)'


    Error handling patterns are all optional:

      WAIT_PATTERN: (optional) Detect waiting time
        example: WAIT_PATTERN = r''

      PREMIUM_ONLY_PATTERN: (optional) Check if the file can be downloaded only with a premium account
        example: PREMIUM_ONLY_PATTERN = r'Premium account required'

      ERROR_PATTERN: (optional) Detect any error preventing download
        example: ERROR_PATTERN = r''


    Instead overriding handleFree and handlePremium methods you can define the following patterns for direct download:

      LINK_FREE_PATTERN: (optional) group(1) should be the direct link for free download
        example: LINK_FREE_PATTERN = r'<div class="link"><a href="(.+?)"'

      LINK_PREMIUM_PATTERN: (optional) group(1) should be the direct link for premium download
        example: LINK_PREMIUM_PATTERN = r'<div class="link"><a href="(.+?)"'
    """

    NAME_REPLACEMENTS = [("&#?\w+;", fixup)]
    SIZE_REPLACEMENTS = []
    URL_REPLACEMENTS  = []

    TEXT_ENCODING       = False  #: Set to True or encoding name if encoding value in http header is not correct
    COOKIES             = True   #: or False or list of tuples [(domain, name, value)]
    FORCE_CHECK_TRAFFIC = False  #: Set to True to force checking traffic left for premium account
    CHECK_DIRECT_LINK   = None   #: Set to True to check for direct link, set to None to do it only if self.account is True
    MULTI_HOSTER        = False  #: Set to True to leech other hoster link (according its multihoster hook if available)


    @classmethod
    def parseInfos(cls, urls):
        for url in urls:
            url = replace_patterns(url, cls.FILE_URL_REPLACEMENTS if hasattr(cls, "FILE_URL_REPLACEMENTS") else cls.URL_REPLACEMENTS)  #@TODO: Remove FILE_URL_REPLACEMENTS check in 0.4.10
            yield cls.getInfo(url)


    @classmethod
    def getInfo(cls, url="", html=""):
        info = {'name': urlparse(unquote(url)).path.split('/')[-1] or _("Unknown"), 'size': 0, 'status': 3, 'url': url}

        if not html:
            try:
                if not url:
                    info['error']  = "missing url"
                    info['status'] = 1
                    raise

                try:
                    html = getURL(url, cookies=cls.COOKIES, decode=not cls.TEXT_ENCODING)

                    if isinstance(cls.TEXT_ENCODING, basestring):
                        html = unicode(html, cls.TEXT_ENCODING)

                except BadHeader, e:
                    info['error'] = "%d: %s" % (e.code, e.content)

                    if e.code is 404:
                        info['status'] = 1
                        raise

                    if e.code is 503:
                        info['status'] = 6
                        raise
            except:
                return info

        online = False

        if hasattr(cls, "OFFLINE_PATTERN") and re.search(cls.OFFLINE_PATTERN, html):
            info['status'] = 1

        elif hasattr(cls, "FILE_OFFLINE_PATTERN") and re.search(cls.FILE_OFFLINE_PATTERN, html):  #@TODO: Remove in 0.4.10
            info['status'] = 1

        elif hasattr(cls, "TEMP_OFFLINE_PATTERN") and re.search(cls.TEMP_OFFLINE_PATTERN, html):
            info['status'] = 6

        else:
            try:
                info['pattern'] = re.match(cls.__pattern__, url).groupdict()  #: pattern groups will be saved here, please save api stuff to info['api']
            except:
                pass

            for pattern in ("FILE_INFO_PATTERN", "INFO_PATTERN",
                            "FILE_NAME_PATTERN", "NAME_PATTERN",
                            "FILE_SIZE_PATTERN", "SIZE_PATTERN",
                            "HASHSUM_PATTERN"):  #@TODO: Remove old patterns starting with "FILE_" in 0.4.10
                try:
                    attr = getattr(cls, pattern)
                    dict = re.search(attr, html).groupdict()

                    if all(True for k in dict if k not in info['pattern']):
                        info['pattern'].update(dict)

                except AttributeError:
                    continue

                else:
                    online = True

        if online:
            info['status'] = 2

            if 'N' in info['pattern']:
                info['name'] = replace_patterns(unquote(info['pattern']['N'].strip()),
                                                cls.FILE_NAME_REPLACEMENTS if hasattr(cls, "FILE_NAME_REPLACEMENTS") else cls.NAME_REPLACEMENTS)  #@TODO: Remove FILE_NAME_REPLACEMENTS check in 0.4.10

            if 'S' in info['pattern']:
                size = replace_patterns(info['pattern']['S'] + info['pattern']['U'] if 'U' in info else info['pattern']['S'],
                                        cls.FILE_SIZE_REPLACEMENTS if hasattr(cls, "FILE_SIZE_REPLACEMENTS") else cls.SIZE_REPLACEMENTS)  #@TODO: Remove FILE_SIZE_REPLACEMENTS check in 0.4.10
                info['size'] = parseFileSize(size)

            elif isinstance(info['size'], basestring):
                unit = info['units'] if 'units' in info else None
                info['size'] = parseFileSize(info['size'], unit)

            if 'H' in info['pattern']:
                hashtype = info['pattern']['T'] if 'T' in info['pattern'] else "hash"
                info[hashtype] = info['pattern']['H']

        return info


    def setup(self):
        self.resumeDownload = self.multiDL = self.premium


    def prepare(self):
        self.info      = {}
        self.link      = ""     #@TODO: Move to hoster class in 0.4.10
        self.directDL  = False  #@TODO: Move to hoster class in 0.4.10
        self.multihost = False  #@TODO: Move to hoster class in 0.4.10

        self.req.setOption("timeout", 120)

        if isinstance(self.COOKIES, list):
            set_cookies(self.req.cj, self.COOKIES)

        if (self.MULTI_HOSTER
            and (self.__pattern__ != self.core.pluginManager.hosterPlugins[self.__name__]['pattern']
                 or re.match(self.__pattern__, self.pyfile.url) is None)):

            self.logInfo("Multi hoster detected")

            if self.account:
                self.multihost = True
                return
            else:
                self.fail(_("Only registered or premium users can use url leech feature"))

        if self.CHECK_DIRECT_LINK is None:
            self.directDL = bool(self.account)

        self.pyfile.url = replace_patterns(self.pyfile.url,
                                           self.FILE_URL_REPLACEMENTS if hasattr(self, "FILE_URL_REPLACEMENTS") else self.URL_REPLACEMENTS)  #@TODO: Remove FILE_URL_REPLACEMENTS check in 0.4.10


    def preload(self):
        self.html = self.load(self.pyfile.url, cookies=bool(self.COOKIES), decode=not self.TEXT_ENCODING)

        if isinstance(self.TEXT_ENCODING, basestring):
            self.html = unicode(self.html, self.TEXT_ENCODING)


    def process(self, pyfile):
        self.prepare()

        if self.multihost:
            self.logDebug("Looking for leeched download link...")
            self.handleMulti()

        elif self.directDL:
            self.logDebug("Looking for direct download link...")
            self.handleDirect()

        if not self.link:
            self.preload()

            if self.html is None:
                self.fail(_("No html retrieved"))

            self.checkErrors()

            premium_only = 'error' in self.info and self.info['error'] == "premium-only"

            self._updateInfo(self.getInfo(pyfile.url, self.html))

            self.checkNameSize()

            #: Usually premium only pages doesn't show any file information
            if not premium_only:
                self.checkStatus()

            if self.premium and (not self.FORCE_CHECK_TRAFFIC or self.checkTrafficLeft()):
                self.logDebug("Handled as premium download")
                self.handlePremium()

            elif premium_only:
                self.fail(_("Link require a premium account to be handled"))

            else:
                self.logDebug("Handled as free download")
                self.handleFree()

        self.downloadLink(self.link)
        self.checkFile()


    def downloadLink(self, link):
        if not link:
            return

        self.download(link, disposition=True)


    def checkFile(self):
        if self.checkDownload({'empty': re.compile(r"^$")}) is "empty":  #@TODO: Move to hoster in 0.4.10
            self.fail(_("Empty file"))


    def checkErrors(self):
        if hasattr(self, 'ERROR_PATTERN'):
            m = re.search(self.ERROR_PATTERN, self.html)
            if m:
                errmsg = self.info['error'] = m.group(1)
                self.error(errmsg)

        if hasattr(self, 'PREMIUM_ONLY_PATTERN'):
            m = re.search(self.PREMIUM_ONLY_PATTERN, self.html)
            if m:
                self.info['error'] = "premium-only"
                return

        if hasattr(self, 'WAIT_PATTERN'):
            m = re.search(self.WAIT_PATTERN, self.html)
            if m:
                wait_time = sum([int(v) * {"hr": 3600, "hour": 3600, "min": 60, "sec": 1}[u.lower()] for v, u in
                                 re.findall(r'(\d+)\s*(hr|hour|min|sec)', m, re.I)])
                self.wait(wait_time, False)
                return

        self.info.pop('error', None)


    def checkStatus(self):
        status = self.info['status']

        if status is 1:
            self.offline()

        elif status is 6:
            self.tempOffline()

        elif status is not 2:
            self.logInfo(_("File status: %s") % statusMap[status],
                         _("File info: %s")   % self.info)
            self.error(_("No file info retrieved"))


    def checkNameSize(self):
        name = self.info['name']
        size = self.info['size']
        url  = self.info['url']

        if name and name != url:
            self.pyfile.name = name
        else:
            self.pyfile.name = name = self.info['name'] = urlparse(name).path.split('/')[-1]

        if size > 0:
            self.pyfile.size = size
        else:
            size = "Unknown"

        self.logDebug("File name: %s" % name,
                      "File size: %s" % size)


    def checkInfo(self):
        self.checkErrors()

        self._updateInfo(self.getInfo(self.pyfile.url, self.html or ""))

        self.checkNameSize()
        self.checkStatus()


    #: Deprecated
    def getFileInfo(self):
        self.info = {}
        self.checkInfo()
        return self.info


    def _updateInfo(self, info):
        self.logDebug(_("File info (before update): %s") % self.info)
        self.info.update(info)
        self.logDebug(_("File info (after update): %s")  % self.info)


    def handleDirect(self):
        link = _isDirectLink(self, self.pyfile.url, self.resumeDownload)

        if link:
            self.logInfo(_("Direct download link detected"))

            self.link = link

            self._updateInfo(self.getInfo(self.pyfile.url))
            self.checkNameSize()
        else:
            self.logDebug(_("Direct download link not found"))


    def handleMulti(self):  #: Multi-hoster handler
        pass


    def handleFree(self):
        if not hasattr(self, 'LINK_FREE_PATTERN'):
            self.fail(_("Free download not implemented"))

        try:
            m = re.search(self.LINK_FREE_PATTERN, self.html)
            if m is None:
                self.error(_("Free download link not found"))

            self.link = m.group(1)

        except Exception, e:
            self.fail(e)


    def handlePremium(self):
        if not hasattr(self, 'LINK_PREMIUM_PATTERN'):
            self.fail(_("Premium download not implemented"))

        try:
            m = re.search(self.LINK_PREMIUM_PATTERN, self.html)
            if m is None:
                self.error(_("Premium download link not found"))

            self.link = m.group(1)

        except Exception, e:
            self.fail(e)


    def longWait(self, wait_time=None, max_tries=3):
        if wait_time and isinstance(wait_time, (int, long, float)):
            time_str  = "%dh %dm" % divmod(wait_time / 60, 60)
        else:
            wait_time = 900
            time_str  = _("(unknown time)")
            max_tries = 100

        self.logInfo(_("Download limit reached, reconnect or wait %s") % time_str)

        self.setWait(wait_time, True)
        self.wait()
        self.retry(max_tries=max_tries, reason=_("Download limit reached"))


    def parseHtmlForm(self, attr_str="", input_names={}):
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
