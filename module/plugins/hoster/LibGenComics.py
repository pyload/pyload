# -*- coding: utf-8 -*-

import re
import BeautifulSoup
import urlparse

from module.network.HTTPRequest import BadHeader

from .Http import Http

class LibGenComics(Http):
    __name__ = "LibGenComics"
    __type__ = "hoster"
    __version__ = "0.12"
    __status__ = "testing"

    __pattern__ = r'https?://libgen.io/comics0/.*'
    __config__ = [
        ("activated", "bool", "Activated", True),
        ("max_recursions", "int", "Maximum directories to recurse into", 100)
    ]

    __description__ = """Download comics from libgen.io respecting throttling limits"""
    __license__ = "GPLv3"
    __authors__ = [("Yann Jouanique", "yann.jouanique@gmail.com")]

    recursions = 1

    def setup(self):
        self.chunk_limit = -1
        self.resume_download = True
        self.multiDL = False

    def process(self, pyfile):
        url = re.sub(r'^(jd|py)', "http", pyfile.url)

        if not re.match(r'.*\/$',url):
            # It's a single direct download link, donwload it
            self.log_debug("Link is a single file")
            for _i in range(2):
                try:
                    self.download(url, ref=False, disposition=True, fixurl=False)
                except BadHeader, e:
                    if e.code not in (401, 403, 404, 410):
                        raise

                if self.req.code in (404, 410):
                    self.offline()
                else:
                    break

            self.check_download()
        
        else:
            # It's a directory list, parse the list
            self.log_debug("Link is a directory")
            max = self.config.get('max_recursions')

            html = self.load(pyfile.url, decode=False)
            if html:
                soup = BeautifulSoup.BeautifulSoup(html)
                if soup:
                    self.log_debug("Got HTML page - Title = " + soup.title.string)
                    domain = urlparse.urlparse(pyfile.url).netloc
                    links = []

                    # Get all links, excluding parent folder
                    for link in soup.findAll("a", href=re.compile("^(?!\.\./).*")):
                        nlinks = len(pyfile.package().getChildren())
                        if nlinks >= max:
                            self.log_warning("Reached max link count for this package (%d/%d), skipping" % (nlinks,max))
                            break

                        self.log_debug("Detected new link")

                        href = link.get('href')
                        self.log_debug("href: "+href)

                        abslink = urlparse.urljoin(pyfile.url,href)
                        self.log_debug("Abslink: "+abslink)

                        new_domain = urlparse.urlparse(abslink).netloc
                        self.log_debug("Domain: "+new_domain)

                        if new_domain != domain:
                            self.log_debug("Different domain, ignoring link...")
                            break

                        self.log_debug("Adding link "+abslink)
                        self.pyload.api.addFiles(pyfile.package().id, [abslink])

            self.skip("Link was a directory listing")


