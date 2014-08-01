# -*- coding: utf-8 -*-

import pycurl
import re

from urllib import quote, unquote
from urlparse import urlparse

from module.plugins.Hoster import Hoster


class Ftp(Hoster):
    __name__ = "Ftp"
    __type__ = "hoster"
    __version__ = "0.41"

    __description__ = """Download from ftp directory"""
    __author_name__ = ("jeix", "mkaay", "zoidberg")
    __author_mail__ = ("jeix@hasnomail.com", "mkaay@mkaay.de", "zoidberg@mujmail.cz")


    def setup(self):
        self.chunkLimit = -1
        self.resumeDownload = True

    def process(self, pyfile):
        parsed_url = urlparse(pyfile.url)
        netloc = parsed_url.netloc

        pyfile.name = parsed_url.path.rpartition('/')[2]
        try:
            pyfile.name = unquote(str(pyfile.name)).decode('utf8')
        except:
            pass

        if not "@" in netloc:
            servers = [x['login'] for x in self.account.getAllAccounts()] if self.account else []

            if netloc in servers:
                self.logDebug("Logging on to %s" % netloc)
                self.req.addAuth(self.account.accounts[netloc]['password'])
            else:
                for pwd in pyfile.package().password.splitlines():
                    if ":" in pwd:
                        self.req.addAuth(pwd.strip())
                        break

        self.req.http.c.setopt(pycurl.NOBODY, 1)

        try:
            response = self.load(pyfile.url)
        except pycurl.error, e:
            self.fail("Error %d: %s" % e.args)

        self.req.http.c.setopt(pycurl.NOBODY, 0)
        self.logDebug(self.req.http.header)

        m = re.search(r"Content-Length:\s*(\d+)", response)
        if m:
            pyfile.size = int(m.group(1))
            self.download(pyfile.url)
        else:
            #Naive ftp directory listing
            if re.search(r'^25\d.*?"', self.req.http.header, re.M):
                pyfile.url = pyfile.url.rstrip('/')
                pkgname = "/".join(pyfile.package().name, urlparse(pyfile.url).path.rpartition('/')[2])
                pyfile.url += '/'
                self.req.http.c.setopt(48, 1)  # CURLOPT_DIRLISTONLY
                response = self.load(pyfile.url, decode=False)
                links = [pyfile.url + quote(x) for x in response.splitlines()]
                self.logDebug("LINKS", links)
                self.core.api.addPackage(pkgname, links)
            else:
                self.fail("Unexpected server response")
