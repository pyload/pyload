# -*- coding: utf-8 -*-

"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.

    @author: zoidberg
"""
from urlparse import urlparse
import re
from time import time

from module.plugins.Hoster import Hoster
from module.utils import html_unescape, fixup, parseFileSize
from module.network.RequestFactory import getURL
from module.network.CookieJar import CookieJar


def replace_patterns(string, ruleslist):
    for r in ruleslist:
        rf, rt = r
        string = re.sub(rf, rt, string)
        #self.logDebug(rf, rt, string)
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
                if value is None:
                    inputs[name] = inputtag.group(3) or ''
                else:
                    inputs[name] = value

        if isinstance(input_names, dict):
            # check input attributes
            for key, val in input_names.items():
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


def parseFileInfo(self, url='', html=''):
    info = {"name": url, "size": 0, "status": 3}

    if hasattr(self, "pyfile"):
        url = self.pyfile.url

    if hasattr(self, "req") and self.req.http.code == '404':
        info['status'] = 1
    else:
        if not html and hasattr(self, "html"):
            html = self.html
        if isinstance(self.SH_BROKEN_ENCODING, (str, unicode)):
            html = unicode(html, self.SH_BROKEN_ENCODING)
            if hasattr(self, "html"):
                self.html = html

        if hasattr(self, "FILE_OFFLINE_PATTERN") and re.search(self.FILE_OFFLINE_PATTERN, html):
            # File offline
            info['status'] = 1
        else:
            online = False
            try:
                info.update(re.match(self.__pattern__, url).groupdict())
            except:
                pass

            for pattern in ("FILE_INFO_PATTERN", "FILE_NAME_PATTERN", "FILE_SIZE_PATTERN"):
                try:
                    info.update(re.search(getattr(self, pattern), html).groupdict())
                    online = True
                except AttributeError:
                    continue

            if online:
                # File online, return name and size
                info['status'] = 2
                if 'N' in info:
                    info['name'] = replace_patterns(info['N'], self.FILE_NAME_REPLACEMENTS)
                if 'S' in info:
                    size = replace_patterns(info['S'] + info['U'] if 'U' in info else info['S'],
                                            self.FILE_SIZE_REPLACEMENTS)
                    info['size'] = parseFileSize(size)
                elif isinstance(info['size'], (str, unicode)):
                    if 'units' in info:
                        info['size'] += info['units']
                    info['size'] = parseFileSize(info['size'])

    if hasattr(self, "file_info"):
        self.file_info = info

    return info['name'], info['size'], info['status'], url


def create_getInfo(plugin):
    def getInfo(urls):
        for url in urls:
            cj = CookieJar(plugin.__name__)
            if isinstance(plugin.SH_COOKIES, list):
                set_cookies(cj, plugin.SH_COOKIES)
            file_info = parseFileInfo(plugin, url, getURL(replace_patterns(url, plugin.FILE_URL_REPLACEMENTS),
                                                          decode=not plugin.SH_BROKEN_ENCODING, cookies=cj))
            yield file_info

    return getInfo


def timestamp():
    return int(time() * 1000)


class PluginParseError(Exception):
    def __init__(self, msg):
        Exception.__init__(self)
        self.value = 'Parse error (%s) - plugin may be out of date' % msg

    def __str__(self):
        return repr(self.value)


class SimpleHoster(Hoster):
    __name__ = "SimpleHoster"
    __version__ = "0.33"
    __pattern__ = None
    __type__ = "hoster"
    __description__ = """Base hoster plugin"""
    __author_name__ = ("zoidberg", "stickell")
    __author_mail__ = ("zoidberg@mujmail.cz", "l.stickell@yahoo.it")
    """
    These patterns should be defined by each hoster:
    FILE_INFO_PATTERN = r'(?P<N>file_name) (?P<S>file_size) (?P<U>units)'
    or FILE_NAME_PATTERN = r'(?P<N>file_name)'
    and FILE_SIZE_PATTERN = r'(?P<S>file_size) (?P<U>units)'
    FILE_OFFLINE_PATTERN = r'File (deleted|not found)'
    TEMP_OFFLINE_PATTERN = r'Server maintainance'

    You can also define a PREMIUM_ONLY_PATTERN to detect links that can be downloaded only with a premium account.
    """

    FILE_SIZE_REPLACEMENTS = []
    FILE_NAME_REPLACEMENTS = [("&#?\w+;", fixup)]
    FILE_URL_REPLACEMENTS = []

    SH_BROKEN_ENCODING = False  # Set to True or encoding name if encoding in http header is not correct
    SH_COOKIES = True  # or False or list of tuples [(domain, name, value)]
    SH_CHECK_TRAFFIC = False  # True = force check traffic left for a premium account

    def init(self):
        self.file_info = {}

    def setup(self):
        self.resumeDownload = self.multiDL = self.premium
        if isinstance(self.SH_COOKIES, list):
            set_cookies(self.req.cj, self.SH_COOKIES)

    def process(self, pyfile):
        pyfile.url = replace_patterns(pyfile.url, self.FILE_URL_REPLACEMENTS)
        self.req.setOption("timeout", 120)
        # Due to a 0.4.9 core bug self.load would keep previous cookies even if overridden by cookies parameter.
        # Workaround using getURL. Can be reverted in 0.5 as the cookies bug has been fixed.
        self.html = getURL(pyfile.url, decode=not self.SH_BROKEN_ENCODING, cookies=self.SH_COOKIES)
        premium_only = hasattr(self, 'PREMIUM_ONLY_PATTERN') and re.search(self.PREMIUM_ONLY_PATTERN, self.html)
        if not premium_only:  # Usually premium only pages doesn't show the file information
            self.getFileInfo()

        if self.premium and (not self.SH_CHECK_TRAFFIC or self.checkTrafficLeft()):
            self.handlePremium()
        elif premium_only:
            self.fail("This link require a premium account")
        else:
            # This line is required due to the getURL workaround. Can be removed in 0.5
            self.html = self.load(pyfile.url, decode=not self.SH_BROKEN_ENCODING, cookies=self.SH_COOKIES)
            self.handleFree()

    def load(self, url, get={}, post={}, ref=True, cookies=True, just_header=False, decode=False):
        if type(url) == unicode:
            url = url.encode('utf8')
        return Hoster.load(self, url=url, get=get, post=post, ref=ref, cookies=cookies,
                           just_header=just_header, decode=decode)

    def getFileInfo(self):
        self.logDebug("URL: %s" % self.pyfile.url)
        if hasattr(self, "TEMP_OFFLINE_PATTERN") and re.search(self.TEMP_OFFLINE_PATTERN, self.html):
            self.tempOffline()

        name, size, status = parseFileInfo(self)[:3]

        if status == 1:
            self.offline()
        elif status != 2:
            self.logDebug(self.file_info)
            self.parseError('File info')

        if name:
            self.pyfile.name = name
        else:
            self.pyfile.name = html_unescape(urlparse(self.pyfile.url).path.split("/")[-1])

        if size:
            self.pyfile.size = size
        else:
            self.logError("File size not parsed")

        self.logDebug("FILE NAME: %s FILE SIZE: %s" % (self.pyfile.name, self.pyfile.size))
        return self.file_info

    def handleFree(self):
        self.fail("Free download not implemented")

    def handlePremium(self):
        self.fail("Premium download not implemented")

    def parseError(self, msg):
        raise PluginParseError(msg)

    def longWait(self, wait_time=None, max_tries=3):
        if wait_time and isinstance(wait_time, (int, long, float)):
            time_str = "%dh %dm" % divmod(wait_time / 60, 60)
        else:
            wait_time = 900
            time_str = "(unknown time)"
            max_tries = 100

        self.logInfo("Download limit reached, reconnect or wait %s" % time_str)

        self.setWait(wait_time, True)
        self.wait()
        self.retry(max_tries=max_tries, reason="Download limit reached")

    def parseHtmlForm(self, attr_str='', input_names=None):
        return parseHtmlForm(attr_str, self.html, input_names)

    def checkTrafficLeft(self):
        traffic = self.account.getAccountInfo(self.user, True)["trafficleft"]
        if traffic == -1:
            return True
        size = self.pyfile.size / 1024
        self.logInfo("Filesize: %i KiB, Traffic left for user %s: %i KiB" % (size, self.user, traffic))
        return size <= traffic

    # TODO: Remove in 0.5
    def wait(self, seconds=False, reconnect=False):
        if seconds:
            self.setWait(seconds, reconnect)
        super(SimpleHoster, self).wait()
