# -*- coding: utf-8 -*-
#@author: mkaay

from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()
from builtins import str
from urllib.parse import urlparse
from urllib.parse import quote, unquote
import pycurl
import re

from pyload.plugins.hoster import Hoster


class Ftp(Hoster):
    __name__ = "Ftp"
    __version__ = "0.41"
    __pattern__ = r'(ftps?|sftp)://(.*?:.*?@)?.*?/.*'  # ftp://user:password@ftp.server.org/path/to/file
    __type__ = "hoster"
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
        except Exception:
            pass

        if not "@" in netloc:
            servers = [x['login'] for x in self.account.getAllAccounts()] if self.account else []

            if netloc in servers:
                self.logDebug("Logging on to %s" % netloc)
                self.req.addAuth(self.account.accounts[netloc]["password"])
            else:
                for pwd in pyfile.package().password.splitlines():
                    if ":" in pwd:
                        self.req.addAuth(pwd.strip())
                        break

        self.req.http.c.setopt(pycurl.NOBODY, 1)

        try:
            response = self.load(pyfile.url)
        except pycurl.error as e:
            self.fail("Error %d: %s" % e.args)

        self.req.http.c.setopt(pycurl.NOBODY, 0)
        self.logDebug(self.req.http.header)

        found = re.search(r"Content-Length:\s*(\d+)", response)
        if found:
            pyfile.size = int(found.group(1))
            self.download(pyfile.url)
        else:
            #Naive ftp directory listing
            if re.search(r'^25\d.*?"', self.req.http.header, re.M):
                pyfile.url = pyfile.url.rstrip('/')
                pkgname = "/".join((pyfile.package().name, urlparse(pyfile.url).path.rpartition('/')[2]))
                pyfile.url += '/'
                self.req.http.c.setopt(48, 1)  # CURLOPT_DIRLISTONLY
                response = self.load(pyfile.url, decode=False)
                links = [pyfile.url + quote(x) for x in response.splitlines()]
                self.logDebug("LINKS", links)
                self.core.api.addPackage(pkgname, links, 1)
                #self.core.files.addLinks(links, pyfile.package().id)
            else:
                self.fail("Unexpected server response")
