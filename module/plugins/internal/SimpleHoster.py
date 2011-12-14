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
from re import search, sub

from module.plugins.Hoster import Hoster
from module.utils import html_unescape, parseFileSize
from module.network.RequestFactory import getURL

def reSub(string, ruleslist):
    for r in ruleslist:
        rf, rt = r
        string = sub(rf, rt, string)
    return string

def parseFileInfo(self, url = '', html = '', infomode = False):
    if not html and hasattr(self, "html"): html = self.html
    info = {"name" : url, "size" : 0, "status" : 3}
    online = False

    if hasattr(self, "FILE_OFFLINE_PATTERN") and search(self.FILE_OFFLINE_PATTERN, html):
        # File offline
        info['status'] = 1
    else:
        for pattern in ("FILE_INFO_PATTERN", "FILE_NAME_PATTERN", "FILE_SIZE_PATTERN"):
            try:
                info = dict(info, **search(getattr(self, pattern), html).groupdict())
                online = True
            except AttributeError:
                continue

        if online:
            # File online, return name and size
            info['status'] = 2
            if 'N' in info: info['name'] = reSub(info['N'], self.FILE_NAME_REPLACEMENTS)
            if 'S' in info:
                size = reSub(info['S'] + info['U'] if 'U' in info else info['S'], self.FILE_SIZE_REPLACEMENTS)
                info['size'] = parseFileSize(size)
            elif isinstance(info['size'], (str, unicode)):
                if 'units' in info: info['size'] += info['units']
                info['size'] = parseFileSize(info['size'])

    if infomode:
        return info
    else:
        return info['name'], info['size'], info['status'], url

def create_getInfo(plugin):
    def getInfo(urls):
        for url in urls:
            file_info = parseFileInfo(plugin, url, getURL(reSub(url, plugin.FILE_URL_REPLACEMENTS), decode=True))
            yield file_info
    return getInfo

class PluginParseError(Exception):
    def __init__(self, msg):
        Exception.__init__(self)
        self.value = 'Parse error (%s) - plugin may be out of date' % msg
    def __str__(self):
        return repr(self.value)

class SimpleHoster(Hoster):
    __name__ = "SimpleHoster"
    __version__ = "0.14"
    __pattern__ = None
    __type__ = "hoster"
    __description__ = """Base hoster plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")
    """
    These patterns should be defined by each hoster:
    FILE_INFO_PATTERN = r'(?P<N>file_name) (?P<S>file_size) (?P<U>units)'
    or FILE_NAME_INFO = r'(?P<N>file_name)'
    and FILE_SIZE_INFO = r'(?P<S>file_size) (?P<U>units)'
    FILE_OFFLINE_PATTERN = r'File (deleted|not found)'
    TEMP_OFFLINE_PATTERN = r'Server maintainance'
    """

    FILE_SIZE_REPLACEMENTS = []
    FILE_NAME_REPLACEMENTS = []
    FILE_URL_REPLACEMENTS = []

    def setup(self):
        self.resumeDownload = self.multiDL = True if self.account else False

    def process(self, pyfile):
        pyfile.url = reSub(pyfile.url, self.FILE_URL_REPLACEMENTS)
        self.html = self.load(pyfile.url, decode = True)
        self.file_info = self.getFileInfo()
        if self.account:
            self.handlePremium()
        else:
            self.handleFree()

    def getFileInfo(self):
        self.logDebug("URL: %s" % self.pyfile.url)
        if hasattr(self, "TEMP_OFFLINE_PATTERN") and search(self.TEMP_OFFLINE_PATTERN, self.html):
            self.tempOffline()

        file_info = parseFileInfo(self, infomode = True)
        if file_info['status'] == 1:
            self.offline()
        elif file_info['status'] != 2:
            self.logDebug(file_info)
            self.parseError('File info')

        if file_info['name']:
            self.pyfile.name = file_info['name']
        else:
            self.pyfile.name = html_unescape(urlparse(self.pyfile.url).path.split("/")[-1])

        if file_info['size']:
            self.pyfile.size = file_info['size']
        else:
            self.logError("File size not parsed")

        self.logDebug("FILE NAME: %s FILE SIZE: %s" % (self.pyfile.name, self.pyfile.size))
        return file_info

    def handleFree(self):
        self.fail("Free download not implemented")

    def handlePremium(self):
        self.fail("Premium download not implemented")

    def parseError(self, msg):
        raise PluginParseError(msg)