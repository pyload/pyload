#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

from module.plugins.Crypter import Crypter
from module.lib.BeautifulSoup import BeautifulSoup, BeautifulStoneSoup

class HoerbuchIn(Crypter):
    __name__ = "HoerbuchIn"
    __type__ = "container"
    __pattern__ = r"http://(www\.)?hoerbuch\.in/(blog\.php\?id=|download_(.*)\.html)"
    __version__ = "0.5"
    __description__ = """Hoerbuch.in Container Plugin"""
    __author_name__ = ("spoob", "mkaay")
    __author_mail__ = ("spoob@pyload.org", "mkaay@mkaay.de")

    def decrypt(self, pyfile):
        self.pyfile = pyfile
        
        self.html = self.req.load(self.pyfile.url)
        if re.search(r"Download", self.html) is None:
            self.offline()
        
        soup = BeautifulSoup(self.html, convertEntities=BeautifulStoneSoup.HTML_ENTITIES)
        package_base = soup.find("a", attrs={"href": re.compile(self.__pattern__)}).text
        
        links = {}
        out = re.compile("http://www.hoerbuch.in/cj/out.php\?pct=\d+&url=(http://rs\.hoerbuch\.in/.*)")
        for a in soup.findAll("a", attrs={"href": out}):
            part = int(a.text.replace("Part ", ""))
            if not part in links.keys():
                links[part] = []
            links[part].append(out.search(a["href"]).group(1))
        
        sortedLinks = {}
        for mirrors in links.values():
            decrypted_mirrors = []
            for u in mirrors:
                src = self.load(u)
                decrypted_mirrors.append(re.search('<FORM ACTION="(http://.*?)" METHOD="post"', src).group(1))
            
            results = self.core.pluginManager.parseUrls(decrypted_mirrors)
        
            for url, hoster in results:
                if not sortedLinks.has_key(hoster):
                    sortedLinks[hoster] = []
                sortedLinks[hoster].append(url)
        
        for hoster, urls in sortedLinks.iteritems():
            self.packages.append(("%s (%s)" % (package_base, hoster), urls, self.pyfile.package().folder))

