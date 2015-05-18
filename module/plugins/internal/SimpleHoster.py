# -*- coding: utf-8 -*-

import datetime
import mimetypes
import os
import re
import time
import urllib
import urlparse

from module.PyFile import statusMap as _statusMap
from module.network.CookieJar import CookieJar
from module.network.HTTPRequest import BadHeader
from module.network.RequestFactory import getURL
from module.plugins.Hoster import Hoster
from module.plugins.Plugin import Fail, Retry
from module.utils import fixup, fs_encode, parseFileSize


#@TODO: Adapt and move to PyFile in 0.4.10
statusMap = dict((v, k) for k, v in _statusMap.iteritems())


#@TODO: Remove in 0.4.10 and redirect to self.error instead
def _error(self, reason, type):
        if not reason and not type:
            type = "unknown"

        msg  = _("%s error") % type.strip().capitalize() if type else _("Error")
        msg += (": %s" % reason.strip()) if reason else ""
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
                    inputs[name] = inputtag.group(3) or ""
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


#@TODO: Remove in 0.4.10
def parseFileInfo(plugin, url="", html=""):
    if hasattr(plugin, "getInfo"):
        info = plugin.getInfo(url, html)
        res  = info['name'], info['size'], info['status'], info['url']
    else:
        url   = urllib.unquote(url)
        url_p = urlparse.urlparse(url)
        res   = ((url_p.path.split('/')[-1]
                  or url_p.query.split('=', 1)[::-1][0].split('&', 1)[0]
                  or url_p.netloc.split('.', 1)[0]),
                 0,
                 3 if url else 8,
                 url)

    return res


#@TODO: Remove in 0.4.10
def create_getInfo(plugin):
    def getInfo(urls):
        for url in urls:
            if hasattr(plugin, "URL_REPLACEMENTS"):
                url = replace_patterns(url, plugin.URL_REPLACEMENTS)
            yield parseFileInfo(plugin, url)

    return getInfo


def timestamp():
    return int(time.time() * 1000)


#@TODO: Move to hoster class in 0.4.10
def getFileURL(self, url, follow_location=None):
    link     = ""
    redirect = 1

    if type(follow_location) is int:
        redirect = max(follow_location, 1)
    else:
        redirect = 10

    for i in xrange(redirect):
        try:
            self.logDebug("Redirect #%d to: %s" % (i, url))
            header = self.load(url, just_header=True, decode=True)

        except Exception:  #: Bad bad bad... rewrite this part in 0.4.10
            req = pyreq.getHTTPRequest()
            res = req.load(url, just_header=True, decode=True)

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

            if not urlparse.urlparse(location).scheme:
                url_p    = urlparse.urlparse(url)
                baseurl  = "%s://%s" % (url_p.scheme, url_p.netloc)
                location = urlparse.urljoin(baseurl, location)

            if 'code' in header and header['code'] == 302:
                link = location

            if follow_location:
                url = location
                continue

        else:
            extension = os.path.splitext(urlparse.urlparse(url).path.split('/')[-1])[-1]

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
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=gmt)

    if now.hour is 0 and now.minute < 10:
        midnight = now
    else:
        midnight = now + datetime.timedelta(days=1)

    td = midnight.replace(hour=0, minute=10, second=0, microsecond=0) - now

    if hasattr(td, 'total_seconds'):
        res = td.total_seconds()
    else:  #@NOTE: work-around for python 2.5 and 2.6 missing datetime.timedelta.total_seconds
        res = (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6

    return int(res)


class SimpleHoster(Hoster):
    __name__    = "SimpleHoster"
    __type__    = "hoster"
    __version__ = "1.46"

    __pattern__ = r'^unmatchable$'
    __config__  = [("use_premium", "bool", "Use premium account if available"          , True),
                   ("fallback"   , "bool", "Fallback to free download if premium fails", True)]

    __description__ = """Simple hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


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

      HAPPY_HOUR_PATTERN: (optional)
        example:

      IP_BLOCKED_PATTERN: (optional)
        example:

      DOWNLOAD_LIMIT_PATTERN: (optional)
        example:

      SIZE_LIMIT_PATTERN: (optional)
        example:

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
    DISPOSITION   = True   #: Set to True to use any content-disposition value in http header as file name

    directLink = getFileURL  #@TODO: Remove in 0.4.10


    @classmethod
    def apiInfo(cls, url):
        url   = urllib.unquote(url)
        url_p = urlparse.urlparse(url)
        return {'name'  : (url_p.path.split('/')[-1]
                           or url_p.query.split('=', 1)[::-1][0].split('&', 1)[0]
                           or url_p.netloc.split('.', 1)[0]),
                'size'  : 0,
                'status': 3 if url else 8,
                'url'   : url}


    @classmethod
    def getInfo(cls, url="", html=""):
        info   = cls.apiInfo(url)
        online = True if info['status'] is 2 else False

        try:
            info['pattern'] = re.match(cls.__pattern__, url).groupdict()  #: pattern groups will be saved here

        except Exception:
            info['pattern'] = {}

        if not html and not online:
            if not url:
                info['error']  = "missing url"
                info['status'] = 1

            elif info['status'] is 3:
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
                info['name'] = replace_patterns(urllib.unquote(info['pattern']['N'].strip()),
                                                cls.NAME_REPLACEMENTS)

            if 'S' in info['pattern']:
                size = replace_patterns(info['pattern']['S'] + info['pattern']['U'] if 'U' in info['pattern'] else info['pattern']['S'],
                                        cls.SIZE_REPLACEMENTS)
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

        if not self.getConfig('use_premium', True):
            self.retryFree()

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

        self.pyfile.url = replace_patterns(self.pyfile.url, self.URL_REPLACEMENTS)


    def preload(self):
        self.html = self.load(self.pyfile.url, cookies=bool(self.COOKIES), decode=not self.TEXT_ENCODING)

        if isinstance(self.TEXT_ENCODING, basestring):
            self.html = unicode(self.html, self.TEXT_ENCODING)


    def process(self, pyfile):
        try:
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

            self.downloadLink(self.link, self.DISPOSITION)
            self.checkFile()

        except Fail, e:  #@TODO: Move to PluginThread in 0.4.10
            if self.getConfig('fallback', True) and self.premium:
                self.logWarning(_("Premium download failed"), e)
                self.retryFree()
            else:
                raise Fail(e)


    def downloadLink(self, link, disposition=True):
        if link and isinstance(link, basestring):
            self.correctCaptcha()

            if not urlparse.urlparse(link).scheme:
                url_p   = urlparse.urlparse(self.pyfile.url)
                baseurl = "%s://%s" % (url_p.scheme, url_p.netloc)
                link    = urlparse.urljoin(baseurl, link)

            self.download(link, ref=False, disposition=disposition)


    def checkFile(self, rules={}):
        if self.cTask and not self.lastDownload:
            self.invalidCaptcha()
            self.retry(10, reason=_("Wrong captcha"))

        elif not self.lastDownload or not os.path.exists(fs_encode(self.lastDownload)):
            self.lastDownload = ""
            self.error(self.pyfile.error or _("No file downloaded"))

        else:
            errmsg = self.checkDownload({'Empty file': re.compile(r'\A\s*\Z'),
                                         'Html error': re.compile(r'\A(?:\s*<.+>)?((?:[\w\s]*(?:[Ee]rror|ERROR)\s*\:?)?\s*\d{3})(?:\Z|\s+)')})

            if not errmsg:
                for r, p in [('Html file'    , re.compile(r'\A\s*<!DOCTYPE html')                                ),
                             ('Request error', re.compile(r'([Aa]n error occured while processing your request)'))]:
                    if r not in rules:
                        rules[r] = p

                for r, a in [('Error'       , "ERROR_PATTERN"       ),
                             ('Premium only', "PREMIUM_ONLY_PATTERN"),
                             ('Wait error'  , "WAIT_PATTERN"        )]:
                    if r not in rules and hasattr(self, a):
                        rules[r] = getattr(self, a)

                errmsg = self.checkDownload(rules)

            if not errmsg:
                return

            errmsg = errmsg.strip().capitalize()

            try:
                errmsg += " | " + self.lastCheck.group(1).strip()
            except Exception:
                pass

            self.logWarning("Check result: " + errmsg, "Waiting 1 minute and retry")
            self.retry(3, 60, errmsg)


    def checkErrors(self):
        if not self.html:
            self.logWarning(_("No html code to check"))
            return

        if hasattr(self, 'IP_BLOCKED_PATTERN') and re.search(self.IP_BLOCKED_PATTERN, self.html):
            self.fail(_("Connection from your current IP address is not allowed"))

        elif not self.premium:
            if hasattr(self, 'PREMIUM_ONLY_PATTERN') and re.search(self.PREMIUM_ONLY_PATTERN, self.html):
                self.fail(_("File can be downloaded by premium users only"))

            elif hasattr(self, 'SIZE_LIMIT_PATTERN') and re.search(self.SIZE_LIMIT_PATTERN, self.html):
                self.fail(_("File too large for free download"))

            elif hasattr(self, 'DOWNLOAD_LIMIT_PATTERN') and re.search(self.DOWNLOAD_LIMIT_PATTERN, self.html):
                m = re.search(self.DOWNLOAD_LIMIT_PATTERN, self.html)
                try:
                    errmsg = m.group(1).strip()
                except Exception:
                    errmsg = m.group(0).strip()

                self.info['error'] = re.sub(r'<.*?>', " ", errmsg)
                self.logWarning(self.info['error'])

                if re.search('da(il)?y|today', errmsg, re.I):
                    wait_time = secondsToMidnight(gmt=2)
                else:
                    wait_time = sum(int(v) * {"hr": 3600, "hour": 3600, "min": 60, "sec": 1, "": 1}[u.lower()] for v, u in
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
                self.logWarning(self.info['error'])

                if re.search('limit|wait', errmsg, re.I):
                    if re.search("da(il)?y|today", errmsg):
                        wait_time = secondsToMidnight(gmt=2)
                    else:
                        wait_time = sum(int(v) * {"hr": 3600, "hour": 3600, "min": 60, "sec": 1, "": 1}[u.lower()] for v, u in
                                    re.findall(r'(\d+)\s*(hr|hour|min|sec|)', errmsg, re.I))

                    self.wantReconnect = wait_time > 300
                    self.retry(1, wait_time, _("Download limit exceeded"))

                elif re.search('country', errmsg, re.I):
                    self.fail(_("Connection from your current IP address is not allowed"))

                elif re.search('captcha', errmsg, re.I):
                    self.invalidCaptcha()

                elif re.search('countdown|expired', errmsg, re.I):
                    self.retry(wait_time=60, reason=_("Link expired"))

                elif re.search('maintenance|maintainance', errmsg, re.I):
                    self.tempOffline()

                elif re.search('up to', errmsg, re.I):
                    self.fail(_("File too large for free download"))

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

                wait_time = sum(int(v) * {"hr": 3600, "hour": 3600, "min": 60, "sec": 1, "": 1}[u.lower()] for v, u in
                                re.findall(r'(\d+)\s*(hr|hour|min|sec|)', waitmsg, re.I))
                self.wait(wait_time, wait_time > 300)

        self.info.pop('error', None)


    def checkStatus(self, getinfo=True):
        if not self.info or getinfo:
            self.logDebug("Update file info...")
            self.logDebug("Previous file info: %s" % self.info)
            self.info.update(self.getInfo(self.pyfile.url, self.html))
            self.logDebug("Current file info: %s"  % self.info)

        try:
            status = self.info['status']

            if status is 1:
                self.offline()

            elif status is 6:
                self.tempOffline()

            elif status is 8:
                self.fail(self.info['error'] if 'error' in self.info else _("Failed"))

        finally:
            self.logDebug("File status: %s" % statusMap[status])


    def checkNameSize(self, getinfo=True):
        if not self.info or getinfo:
            self.logDebug("Update file info...")
            self.logDebug("Previous file info: %s" % self.info)
            self.info.update(self.getInfo(self.pyfile.url, self.html))
            self.logDebug("Current file info: %s"  % self.info)

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

        self.logDebug("File name: %s" % self.pyfile.name,
                      "File size: %s byte" % self.pyfile.size if self.pyfile.size > 0 else "File size: Unknown")


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

        self.wait(wait_time, True)
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


    def getConfig(self, option, default=''):  #@TODO: Remove in 0.4.10
        """getConfig with default value - sublass may not implements all config options"""
        try:
            return self.getConf(option)

        except KeyError:
            return default


    def retryFree(self):
        if not self.premium:
            return
        self.premium = False
        self.account = None
        self.req     = self.core.requestFactory.getRequest(self.__name__)
        self.retries = -1
        raise Retry(_("Fallback to free download"))


    #@TODO: Remove in 0.4.10
    def wait(self, seconds=0, reconnect=None):
        return _wait(self, seconds, reconnect)


    def error(self, reason="", type="parse"):
        return _error(self, reason, type)
