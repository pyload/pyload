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

import re
import time
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo
from module.common.json_layer import json_loads

def convertDecimalPrefix(m):
    # decimal prefixes used in filesize and traffic
    return ("%%.%df" % {'k': 3, 'M': 6, 'G': 9}[m.group(2)] % float(m.group(1))).replace('.', '')

class UlozTo(SimpleHoster):
    __name__ = "UlozTo"
    __type__ = "hoster"
    __pattern__ = r"http://(\w*\.)?(uloz\.to|ulozto\.(cz|sk|net)|bagruj.cz|zachowajto.pl)/(?:live/)?(?P<id>\w+/[^/?]*)"
    __version__ = "0.94"
    __description__ = """uloz.to"""
    __author_name__ = ("zoidberg")

    FILE_NAME_PATTERN = r'<a href="#download" class="jsShowDownload">(?P<N>[^<]+)</a>'
    FILE_SIZE_PATTERN = r'<span id="fileSize">.*?(?P<S>[0-9.]+\s[kMG]?B)</span>'
    FILE_INFO_PATTERN = r'<p>File <strong>(?P<N>[^<]+)</strong> is password protected</p>'
    FILE_OFFLINE_PATTERN = r'<title>404 - Page not found</title>|<h1 class="h1">File (has been deleted|was banned)</h1>'
    FILE_SIZE_REPLACEMENTS = [('([0-9.]+)\s([kMG])B', convertDecimalPrefix)]
    FILE_URL_REPLACEMENTS = [(r"(?<=http://)([^/]+)", "www.ulozto.net")]

    PASSWD_PATTERN = r'<div class="passwordProtectedFile">'
    VIPLINK_PATTERN = r'<a href="[^"]*\?disclaimer=1" class="linkVip">'
    FREE_URL_PATTERN = r'<div class="freeDownloadForm"><form action="([^"]+)"'
    PREMIUM_URL_PATTERN = r'<div class="downloadForm"><form action="([^"]+)"'

    def setup(self):
        self.multiDL = self.premium
        self.resumeDownload = True

    def process(self, pyfile):
        pyfile.url = re.sub(r"(?<=http://)([^/]+)", "www.ulozto.net", pyfile.url)
        self.html = self.load(pyfile.url, decode=True, cookies=True)

        passwords = self.getPassword().splitlines()
        while self.PASSWD_PATTERN in self.html:
            if passwords:
                password = passwords.pop(0)
                self.logInfo("Password protected link, trying " + password)
                self.html = self.load(pyfile.url, get={"do": "passwordProtectedForm-submit"},
                                      post={"password": password, "password_send": 'Send'}, cookies=True)
            else:
                self.fail("No or incorrect password")

        if re.search(self.VIPLINK_PATTERN, self.html):
            self.html = self.load(pyfile.url, get={"disclaimer": "1"})

        self.file_info = self.getFileInfo()

        if self.premium and self.checkTrafficLeft():
            self.handlePremium()
        else:
            self.handleFree()

        self.doCheckDownload()

    def handleFree(self):
        action, inputs = self.parseHtmlForm('id="frm-downloadDialog-freeDownloadForm"')
        if not action or not inputs:
            self.parseError("free download form")

        # I don't know how to check captcha form changes
        for key in inputs.keys():
            found = re.match("(captcha_value|timestamp|salt|hash)", key)
            if found:
                if found.group(1) == "captcha_value":
                    junk_captcha_value = key
                elif found.group(1) == "timestamp":
                    junk_timestamp = key
                elif found.group(1) == "salt":
                    junk_salt = key
                elif found.group(1) == "hash":
                    junk_hash = key

        if not junk_captcha_value or not junk_timestamp or not junk_salt or not junk_hash:
            self.parseError("CAPTCHA form changed")    

        # get and decrypt captcha
        my_timestamp = int(time.time())
        self.logDebug('my_timestamp = ' + str(my_timestamp))

        xapca = self.load("http://www.ulozto.net/reloadXapca.php", get = { "rnd": str(my_timestamp)})
        self.logDebug('xapca = ' + str(xapca))

        data = json_loads(xapca)
        self.logDebug('image = ' + str(data["image"]))
        self.logDebug('sound = ' + str(data["sound"]))
        self.logDebug('timestamp = ' + str(data["timestamp"]))
        self.logDebug('salt = ' + str(data["salt"]))
        self.logDebug('hash = ' + str(data["hash"]))

        captcha_text = self.decryptCaptcha(str(data["image"]))

        self.multiDL = True

        inputs.update({"timestamp": data["timestamp"], "salt": data["salt"], "hash": data["hash"], "captcha_value": captcha_text})

        self.download("http://www.ulozto.net" + action, post=inputs, cookies=True, disposition=True)

    def handlePremium(self):
        self.download(self.pyfile.url + "?do=directDownload", disposition=True)
        #parsed_url = self.findDownloadURL(premium=True)
        #self.download(parsed_url, post={"download": "Download"})

    def findDownloadURL(self, premium=False):
        msg = "%s link" % ("Premium" if premium else "Free")
        found = re.search(self.PREMIUM_URL_PATTERN if premium else self.FREE_URL_PATTERN, self.html)
        if not found:
            self.parseError(msg)
        parsed_url = "http://www.ulozto.net" + found.group(1)
        self.logDebug("%s: %s" % (msg, parsed_url))
        return parsed_url

    def doCheckDownload(self):
        check = self.checkDownload({
            "wrong_captcha": re.compile(r'<ul class="error">\s*<li>Error rewriting the text.</li>'),
            "offline": re.compile(self.FILE_OFFLINE_PATTERN),
            "passwd": self.PASSWD_PATTERN,
            "server_error": 'src="http://img.ulozto.cz/error403/vykricnik.jpg"',  # paralell dl, server overload etc.
            "not_found": "<title>Ulož.to</title>"
        })

        if check == "wrong_captcha":
            self.delStorage("captcha_id")
            self.delStorage("captcha_text")
            self.invalidCaptcha()
            self.retry(reason="Wrong captcha code")
        elif check == "offline":
            self.offline()
        elif check == "passwd":
            self.fail("Wrong password")
        elif check == "server_error":
            self.logError("Server error, try downloading later")
            self.multiDL = False
            self.setWait(3600, True)
            self.wait()
            self.retry()
        elif check == "not_found":
            self.fail("Server error - file not downloadable")


getInfo = create_getInfo(UlozTo)
