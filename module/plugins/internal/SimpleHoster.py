# -*- coding: utf-8 -*-

import mimetypes
import os
import re

from datetime import datetime, timedelta
from inspect import isclass
from time import time
from urllib import unquote
from urlparse import urljoin, urlparse

from module.PyFile import statusMap as _statusMap
from module.network.CookieJar import CookieJar
from module.network.HTTPRequest import BadHeader
from module.network.RequestFactory import getURL
from module.plugins.Hoster import Hoster
from module.plugins.Plugin import Fail
from module.utils import fixup, fs_encode, parseFileSize


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
    if hasattr(plugin, "getInfo"):
        info = plugin.getInfo(url, html)
        res  = info['name'], info['size'], info['status'], info['url']
    else:
        url  = unquote(url)
        res  = ((urlparse(url).path.split('/')[-1]
                 or urlparse(url).query.split('=', 1)[::-1][0].split('&', 1)[0]
                 or _("Unknown")),
                0,
                3 if url else 8,
                url)

    return res


#@TODO: Remove in 0.4.10
#@NOTE: Every plugin must have own parseInfos classmethod to work with 0.4.10
def create_getInfo(plugin):

    def generator(list):
        for x in list:
            yield x

    if hasattr(plugin, "parseInfos"):
        fn = lambda urls: generator((info['name'], info['size'], info['status'], info['url']) for info in plugin.parseInfos(urls))
    else:
        fn = lambda urls: generator(parseFileInfo(url) for url in urls)

    return fn


def timestamp():
    return int(time() * 1000)


#@TODO: Move to hoster class in 0.4.10
def fileUrl(self, url, follow_location=None):
    link     = ""
    redirect = 1

    if type(follow_location) is int:
        redirect = max(follow_location, 1)
    else:
        redirect = 5

    for i in xrange(redirect):
        try:
            self.logDebug("Redirect #%d to: %s" % (i, url))
            header = self.load(url, ref=True, cookies=True, just_header=True, decode=True)

        except Exception:  #: Bad bad bad...
            req = pyreq.getHTTPRequest()
            res = req.load(url, cookies=True, just_header=True, decode=True)

            req.close()

            header = {"code": req.code}
            for line in res.splitlines():
                line = line.strip()
                if not line or ":" not in line:
                    continue

                key, none, value = line.partition(":")
                key              = key.lower().strip()
                value            = value.strip()

                if key in header:
                    if type(header[key]) == list:
                        header[key].append(value)
                    else:
                        header[key] = [header[key], value]
                else:
                    header[key] = value

        if 'content-disposition' in header:
            link = url

        elif 'location' in header and header['location'].strip():
            location = header['location']

            if not urlparse(location).scheme:
                url_p    = urlparse(url)
                baseurl  = "%s://%s" % (url_p.scheme, url_p.netloc)
                location = urljoin(baseurl, location)

            if 'code' in header and header['code'] == 302:
                link = location

            if follow_location:
                url = location
                continue

        else:
            extension = os.path.splitext(urlparse(url).path.split('/')[-1])[-1]

            if 'content-type' in header and header['content-type'].strip():
                mimetype = header['content-type'].split(';')[0].strip()

            elif extension:
                mimetype = mimetypes.guess_type(extension, False)[0] or "application/octet-stream"

            else:
                mimetype = ""

            if mimetype and (link or 'html' not in mimetype):
                link = url
            else:
                link = ""

        break

    else:
        try:
            self.logError(_("Too many redirects"))
        except Exception:
            pass

    return link


def secondsToMidnight(gmt=0):
    now = datetime.utcnow() + timedelta(hours=gmt)

    if now.hour is 0 and now.minute < 10:
        midnight = now
    else:
        midnight = now + timedelta(days=1)

    td = midnight.replace(hour=0, minute=10, second=0, microsecond=0) - now

    if hasattr(td, 'total_seconds'):
        res = td.total_seconds()
    else:  #@NOTE: work-around for python 2.5 and 2.6 missing timedelta.total_seconds
        res = (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6

    return int(res)


class SimpleHoster(Hoster):
    __name__    = "SimpleHoster"
    __type__    = "hoster"
    __version__ = "1.12"

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

      OFFLINE_PATTERN: (optional) Check if the page is unreachable
        example: OFFLINE_PATTERN = r'File (deleted|not found)'

      TEMP_OFFLINE_PATTERN: (optional) Check if the page is temporarily unreachable
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

    TEXT_ENCODING = False  #: Set to True or encoding name if encoding value in http header is not correct
    COOKIES       = True   #: or False or list of tuples [(domain, name, value)]
    CHECK_TRAFFIC = False  #: Set to True to force checking traffic left for premium account
    DIRECT_LINK   = None   #: Set to True to looking for direct link (as defined in handleDirect method), set to None to do it if self.account is True else False
    MULTI_HOSTER  = False  #: Set to True to leech other hoster link (as defined in handleMulti method)
    LOGIN_ACCOUNT = False  #: Set to True to require account login

    directLink = fileUrl  #@TODO: Remove in 0.4.10


    @classmethod
    def parseInfos(cls, urls):  #@TODO: Built-in in 0.4.10 core, then remove from plugins
        for url in urls:
            url = replace_patterns(url, cls.FILE_URL_REPLACEMENTS if hasattr(cls, "FILE_URL_REPLACEMENTS") else cls.URL_REPLACEMENTS)  #@TODO: Remove FILE_URL_REPLACEMENTS check in 0.4.10
            yield cls.getInfo(url)


    @classmethod
    def apiInfo(cls, url="", get={}, post={}):
        url = unquote(url)
        return {'name'  : (urlparse(url).path.split('/')[-1]
                           or urlparse(url).query.split('=', 1)[::-1][0].split('&', 1)[0]
                           or _("Unknown")),
                'size'  : 0,
                'status': 3 if url else 8,
                'url'   : url}


    @classmethod
    def getInfo(cls, url="", html=""):
        info   = cls.apiInfo(url)
        online = False if info['status'] != 2 else True

        try:
            info['pattern'] = re.match(cls.__pattern__, url).groupdict()  #: pattern groups will be saved here

        except Exception:
            info['pattern'] = {}

        if not html and not online:
            if not url:
                info['error']  = "missing url"
                info['status'] = 1

            elif info['status'] is 3 and not fileUrl(None, url):
                try:
                    html = getURL(url, cookies=cls.COOKIES, decode=not cls.TEXT_ENCODING)

                    if isinstance(cls.TEXT_ENCODING, basestring):
                        html = unicode(html, cls.TEXT_ENCODING)

                except BadHeader, e:
                    info['error'] = "%d: %s" % (e.code, e.content)

                    if e.code is 404:
                        info['status'] = 1

                    elif e.code is 503:
                        info['status'] = 6

        if html:
            if hasattr(cls, "OFFLINE_PATTERN") and re.search(cls.OFFLINE_PATTERN, html):
                info['status'] = 1

            elif hasattr(cls, "FILE_OFFLINE_PATTERN") and re.search(cls.FILE_OFFLINE_PATTERN, html):  #@TODO: Remove in 0.4.10
                info['status'] = 1

            elif hasattr(cls, "TEMP_OFFLINE_PATTERN") and re.search(cls.TEMP_OFFLINE_PATTERN, html):
                info['status'] = 6

            else:
                for pattern in ("FILE_INFO_PATTERN", "INFO_PATTERN",
                                "FILE_NAME_PATTERN", "NAME_PATTERN",
                                "FILE_SIZE_PATTERN", "SIZE_PATTERN",
                                "HASHSUM_PATTERN"):  #@TODO: Remove old patterns starting with "FILE_" in 0.4.10
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
                info['name'] = replace_patterns(unquote(info['pattern']['N'].strip()),
                                                cls.FILE_NAME_REPLACEMENTS if hasattr(cls, "FILE_NAME_REPLACEMENTS") else cls.NAME_REPLACEMENTS)  #@TODO: Remove FILE_NAME_REPLACEMENTS check in 0.4.10

            if 'S' in info['pattern']:
                size = replace_patterns(info['pattern']['S'] + info['pattern']['U'] if 'U' in info['pattern'] else info['pattern']['S'],
                                        cls.FILE_SIZE_REPLACEMENTS if hasattr(cls, "FILE_SIZE_REPLACEMENTS") else cls.SIZE_REPLACEMENTS)  #@TODO: Remove FILE_SIZE_REPLACEMENTS check in 0.4.10
                info['size'] = parseFileSize(size)

            elif isinstance(info['size'], basestring):
                unit = info['units'] if 'units' in info else None
                info['size'] = parseFileSize(info['size'], unit)

            if 'H' in info['pattern']:
                hashtype = info['pattern']['T'] if 'T' in info['pattern'] else "hash"
                info[hashtype] = info['pattern']['H']

        if not info['pattern']:
            info.pop('pattern', None)

        return info


    def setup(self):
        self.resumeDownload = self.multiDL = self.premium


    def prepare(self):
        self.pyfile.error = ""  #@TODO: Remove in 0.4.10

        self.info      = {}
        self.html      = ""
        self.link      = ""     #@TODO: Move to hoster class in 0.4.10
        self.directDL  = False  #@TODO: Move to hoster class in 0.4.10
        self.multihost = False  #@TODO: Move to hoster class in 0.4.10

        if self.LOGIN_ACCOUNT and not self.account:
            self.fail(_("Required account not found"))

        self.req.setOption("timeout", 120)

        if isinstance(self.COOKIES, list):
            set_cookies(self.req.cj, self.COOKIES)

        if (self.MULTI_HOSTER
            and (self.__pattern__ != self.core.pluginManager.hosterPlugins[self.__name__]['pattern']
                 or re.match(self.__pattern__, self.pyfile.url) is None)):
            self.multihost = True
            return

        if self.DIRECT_LINK is None:
            self.directDL = bool(self.account)
        else:
            self.directDL = self.DIRECT_LINK

        self.pyfile.url = replace_patterns(self.pyfile.url,
                                           self.FILE_URL_REPLACEMENTS if hasattr(self, "FILE_URL_REPLACEMENTS") else self.URL_REPLACEMENTS)  #@TODO: Remove FILE_URL_REPLACEMENTS check in 0.4.10


    def preload(self):
        self.html = self.load(self.pyfile.url, cookies=bool(self.COOKIES), decode=not self.TEXT_ENCODING)

        if isinstance(self.TEXT_ENCODING, basestring):
            self.html = unicode(self.html, self.TEXT_ENCODING)


    def process(self, pyfile):
        self.prepare()
        self.checkInfo()

        if self.directDL:
            self.logDebug("Looking for direct download link...")
            self.handleDirect(pyfile)

        if self.multihost and not self.link and not self.lastDownload:
            self.logDebug("Looking for leeched download link...")
            self.handleMulti(pyfile)

            if not self.link and not self.lastDownload:
                self.MULTI_HOSTER = False
                self.retry(1, reason="Multi hoster fails")

        if not self.link and not self.lastDownload:
            self.preload()
            self.checkInfo()

            if self.premium and (not self.CHECK_TRAFFIC or self.checkTrafficLeft()):
                self.logDebug("Handled as premium download")
                self.handlePremium(pyfile)

            elif not self.LOGIN_ACCOUNT or (not self.CHECK_TRAFFIC or self.checkTrafficLeft()):
                self.logDebug("Handled as free download")
                self.handleFree(pyfile)

        self.downloadLink(self.link)
        self.checkFile()


    def downloadLink(self, link, disposition=False):  #@TODO: Set `disposition=True` in 0.4.10
        if link and isinstance(link, basestring):
            self.correctCaptcha()

            if not urlparse(link).scheme:
                url_p   = urlparse(self.pyfile.url)
                baseurl = "%s://%s" % (url_p.scheme, url_p.netloc)
                link    = urljoin(baseurl, link)

            self.download(link, ref=False, disposition=disposition)


    def checkFile(self):
        if self.cTask and not self.lastDownload:
            self.invalidCaptcha()
            self.retry(10, reason=_("Wrong captcha"))

        elif not self.lastDownload or not os.path.exists(fs_encode(self.lastDownload)):
            self.lastDownload = ""
            self.error(self.pyfile.error or _("No file downloaded"))

        else:
            rules = {'empty file': re.compile(r'\A\Z'),
                     'html file' : re.compile(r'\A\s*<!DOCTYPE html'),
                     'html error': re.compile(r'\A\s*(<.+>)?\d{3}(\Z|\s+)')}

            if hasattr(self, 'ERROR_PATTERN'):
                rules['error'] = re.compile(self.ERROR_PATTERN)

            check = self.checkDownload(rules)
            if check:  #@TODO: Move to hoster in 0.4.10
                errmsg = check.strip().capitalize()
                if self.lastCheck:
                    errmsg += " | " + self.lastCheck.group(0).strip()

                self.lastDownload = ""
                self.retry(10, 60, errmsg)


    def checkErrors(self):
        if not self.html:
            self.logWarning(_("No html code to check"))
            return

        if hasattr(self, 'PREMIUM_ONLY_PATTERN') and not self.premium and re.search(self.PREMIUM_ONLY_PATTERN, self.html):
            self.fail(_("Link require a premium account to be handled"))

        elif hasattr(self, 'ERROR_PATTERN'):
            m = re.search(self.ERROR_PATTERN, self.html)
            if m:
                errmsg = self.info['error'] = m.group(1)
                self.error(errmsg)

        elif hasattr(self, 'WAIT_PATTERN'):
            m = re.search(self.WAIT_PATTERN, self.html)
            if m:
                wait_time = sum(int(v) * {"hr": 3600, "hour": 3600, "min": 60, "sec": 1}[u.lower()] for v, u in
                                re.findall(r'(\d+)\s*(hr|hour|min|sec)', m.group(0), re.I))
                self.wait(wait_time, wait_time > 300)
                return

        self.info.pop('error', None)


    def checkStatus(self, getinfo=True):
        if not self.info or getinfo:
            self.logDebug("File info (BEFORE): %s" % self.info)
            self.info.update(self.getInfo(self.pyfile.url, self.html))

        try:
            status = self.info['status']

            if status is 1:
                self.offline()

            elif status is 6:
                self.tempOffline()

            elif status is 8:
                self.fail()

        finally:
            self.logDebug("File status: %s" % statusMap[status],
                          "File info: %s"   % self.info)


    def checkNameSize(self, getinfo=True):
        if not self.info or getinfo:
            self.logDebug("File info (BEFORE): %s" % self.info)
            self.info.update(self.getInfo(self.pyfile.url, self.html))
            self.logDebug("File info (AFTER): %s"  % self.info)

        try:
            url  = self.info['url']
            name = self.info['name']
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

        self.logDebug("File name: %s" % self.pyfile.name,
                      "File size: %s" % self.pyfile.size if self.pyfile.size > 0 else "Unknown")


    def checkInfo(self):
        self.checkNameSize()

        if self.html:
            self.checkErrors()
            self.checkNameSize()

        self.checkStatus(getinfo=False)


    #: Deprecated
    def getFileInfo(self):
        self.info = {}
        self.checkInfo()
        return self.info


    def handleDirect(self, pyfile):
        link = self.directLink(pyfile.url, self.resumeDownload)

        if link:
            self.logInfo(_("Direct download link detected"))

            self.link = link
        else:
            self.logDebug("Direct download link not found")


    def handleMulti(self, pyfile):  #: Multi-hoster handler
        pass


    def handleFree(self, pyfile):
        if not hasattr(self, 'LINK_FREE_PATTERN'):
            self.logError(_("Free download not implemented"))

        m = re.search(self.LINK_FREE_PATTERN, self.html)
        if m is None:
            self.error(_("Free download link not found"))
        else:
            self.link = m.group(1)


    def handlePremium(self, pyfile):
        if not hasattr(self, 'LINK_PREMIUM_PATTERN'):
            self.logError(_("Premium download not implemented"))
            self.logDebug("Handled as free download")
            self.handleFree(pyfile)

        m = re.search(self.LINK_PREMIUM_PATTERN, self.html)
        if m is None:
            self.error(_("Premium download link not found"))
        else:
            self.link = m.group(1)


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
        if not self.account:
            return True

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
