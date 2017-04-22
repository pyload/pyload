# -*- coding: utf-8 -*-
# @author: mkaay

from __future__ import absolute_import, unicode_literals
from future import standard_library

import re
from builtins import int
from urllib.parse import quote, unquote, urlparse

import pycurl

from . import Hoster

standard_library.install_aliases()


class Ftp(Hoster):
    __name__ = "Ftp"
    __version__ = "0.41"
    # ftp://user:password@ftp.server.org/path/to/file
    __pattern__ = r'(ftps?|sftp)://(.*?:.*?@)?.*?/.*'
    __type__ = "hoster"
    __description__ = """Download from ftp directory"""
    __author_name__ = ("jeix", "mkaay", "zoidberg")
    __author_mail__ = ("jeix@hasnomail.com",
                       "mkaay@mkaay.de", "zoidberg@mujmail.cz")

    def setup(self):
        self.chunk_limit = -1
        self.resume_download = True

    def process(self, file):
        parsed_url = urlparse(file.url)
        netloc = parsed_url.netloc

        file.name = unquote(parsed_url.path.rpartition('/')[2])

        if "@" not in netloc:
            servers = [x['login']
                       for x in self.account.get_all_accounts()] if self.account else []

            if netloc in servers:
                self.log_debug("Logging on to {0}".format(netloc))
                self.req.add_auth(self.account.accounts[netloc]['password'])
            else:
                for pwd in file.package().password.splitlines():
                    if ":" in pwd:
                        self.req.add_auth(pwd.strip())
                        break

        self.req.http.c.setopt(pycurl.NOBODY, 1)

        try:
            response = self.load(file.url)
        except pycurl.error as e:
            self.fail(_("Error {0:d}: {1}").format(*e.args))

        self.req.http.c.setopt(pycurl.NOBODY, 0)
        self.log_debug(self.req.http.header)

        found = re.search(r"Content-Length:\s*(\d+)", response)
        if found:
            file.size = int(found.group(1))
            self.download(file.url)
        else:
            # Naive ftp directory listing
            if re.search(r'^25\d.*?"', self.req.http.header, flags=re.M):
                file.url = file.url.rstrip('/')
                pkgname = "/".join((file.package().name,
                                    urlparse(file.url).path.rpartition('/')[2]))
                file.url += '/'
                self.req.http.c.setopt(48, 1)  #: CURLOPT_DIRLISTONLY
                response = self.load(file.url, decode=False)
                links = [file.url + quote(x) for x in response.splitlines()]
                self.log_debug("LINKS", links)
                self.pyload.api.add_package(pkgname, links, 1)
                #self.pyload.files.add_links(links, file.package().id)
            else:
                self.fail(_("Unexpected server response"))
