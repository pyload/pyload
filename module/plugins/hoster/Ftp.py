# -*- coding: utf-8 -*-

import pycurl
import re
import urllib
import urlparse

from module.plugins.Hoster import Hoster


class Ftp(Hoster):
    __name__    = "Ftp"
    __type__    = "hoster"
    __version__ = "0.52"

    __pattern__ = r'(?:ftps?|sftp)://([\w.-]+(:[\w.-]+)?@)?[\w.-]+(:\d+)?/.+'

    __description__ = """Download from ftp directory"""
    __license__     = "GPLv3"
    __authors__     = [("jeix", "jeix@hasnomail.com"),
                       ("mkaay", "mkaay@mkaay.de"),
                       ("zoidberg", "zoidberg@mujmail.cz")]


    def setup(self):
        self.chunkLimit = -1
        self.resumeDownload = True


    def process(self, pyfile):
        parsed_url = urlparse.urlparse(pyfile.url)
        netloc = parsed_url.netloc

        pyfile.name = parsed_url.path.rpartition('/')[2]
        try:
            pyfile.name = urllib.unquote(str(pyfile.name)).decode('utf8')
        except Exception:
            pass

        if not "@" in netloc:
            servers = [x['login'] for x in self.account.getAllAccounts()] if self.account else []

            if netloc in servers:
                self.logDebug("Logging on to %s" % netloc)
                self.req.addAuth(self.account.getAccountInfo(netloc)['password'])
            else:
                pwd = self.getPassword()
                if ':' in pwd:
                    self.req.addAuth(pwd)

        self.req.http.c.setopt(pycurl.NOBODY, 1)

        try:
            res = self.load(pyfile.url)
        except pycurl.error, e:
            self.fail(_("Error %d: %s") % e.args)

        self.req.http.c.setopt(pycurl.NOBODY, 0)
        self.logDebug(self.req.http.header)

        m = re.search(r"Content-Length:\s*(\d+)", res)
        if m:
            pyfile.size = int(m.group(1))
            self.download(pyfile.url)
        else:
            #Naive ftp directory listing
            if re.search(r'^25\d.*?"', self.req.http.header, re.M):
                pyfile.url = pyfile.url.rstrip('/')
                pkgname = "/".join([pyfile.package().name, urlparse.urlparse(pyfile.url).path.rpartition('/')[2]])
                pyfile.url += '/'
                self.req.http.c.setopt(48, 1)  # CURLOPT_DIRLISTONLY
                res = self.load(pyfile.url, decode=False)
                links = [pyfile.url + urllib.quote(x) for x in res.splitlines()]
                self.logDebug("LINKS", links)
                self.core.api.addPackage(pkgname, links)
            else:
                self.fail(_("Unexpected server response"))
