# -*- coding: utf-8 -*-

import re

from urllib import unquote
from urlparse import urljoin, urlparse

from pyload.network.HTTPRequest import BadHeader
from pyload.plugins.internal.SimpleHoster import create_getInfo
from pyload.plugins.Hoster import Hoster


class BasePlugin(Hoster):
    __name    = "BasePlugin"
    __type    = "hoster"
    __version = "0.25"

    __pattern = r'^unmatchable$'

    __description = """Base plugin when any other didnt fit"""
    __license     = "GPLv3"
    __authors     = [("RaNaN", "RaNaN@pyload.org"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    @classmethod
    def getInfo(cls, url="", html=""):  #@TODO: Move to hoster class in 0.4.10
        return {'name': urlparse(unquote(url)).path.split('/')[-1] or _("Unknown"), 'size': 0, 'status': 3 if url else 1, 'url': unquote(url) or ""}


    def setup(self):
        self.chunkLimit = -1
        self.resumeDownload = True


    def process(self, pyfile):
        """main function"""

        pyfile.name = self.getInfo(pyfile.url)['name']

        if not pyfile.url.startswith("http"):
            self.fail(_("No plugin matched"))

        for _i in xrange(5):
            try:
                self.downloadFile(pyfile)

            except BadHeader, e:
                if e.code is 404:
                    self.offline()

                elif e.code in (401, 403):
                    self.logDebug("Auth required", "Received HTTP status code: %d" % e.code)

                    account = self.core.accountManager.getAccountPlugin('Http')
                    servers = [x['login'] for x in account.getAllAccounts()]
                    server  = urlparse(pyfile.url).netloc

                    if server in servers:
                        self.logDebug("Logging on to %s" % server)
                        self.req.addAuth(account.accounts[server]['password'])
                    else:
                        for pwd in self.getPassword().splitlines():
                            if ":" in pwd:
                                self.req.addAuth(pwd.strip())
                                break
                        else:
                            self.fail(_("Authorization required"))
                else:
                    self.fail(e)
            else:
                break
        else:
            self.fail(_("No file downloaded"))  #@TODO: Move to hoster class in 0.4.10

        if self.checkDownload({'empty': re.compile(r"^$")}) is "empty":  #@TODO: Move to hoster in 0.4.10
            self.fail(_("Empty file"))


    def downloadFile(self, pyfile):
        url = pyfile.url

        for i in xrange(1, 7):  #@TODO: retrieve the pycurl.MAXREDIRS value set by req
            header = self.load(url, ref=True, cookies=True, just_header=True, decode=True)

            if 'location' not in header or not header['location']:
                if 'code' in header and header['code'] not in (200, 201, 203, 206):
                    self.logDebug("Received HTTP status code: %d" % header['code'])
                    self.fail(_("File not found"))
                else:
                    break

            location = header['location']

            self.logDebug("Redirect #%d to: %s" % (i, location))

            if urlparse(location).scheme:
                url = location
            else:
                p = urlparse(url)
                base = "%s://%s" % (p.scheme, p.netloc)
                url = urljoin(base, location)
        else:
            self.fail(_("Too many redirects"))

        self.download(unquote(url), disposition=True)
