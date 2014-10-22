# -*- coding: utf-8 -*-
import re

from module.plugins.internal.SimpleCrypter import SimpleCrypter
from BeautifulSoup import BeautifulSoup
from urlparse import urlparse

class Go4Up(SimpleCrypter):

    __name__ = "Go4Up"
    __type__ = "crypter"
    __version__ = "0.1"
    __pattern__ = r"http://(www\.)?go4up.com/dl/\w+.*"
    __config__ = [("preferedHoster", "str", "Prefered hoster list (pipe-separated) ", ""),
              ("ignoredHoster", "str", "Ignored hoster list (pipe-separated) ", "")]
    __description__ = """Go4Up plugin"""
    __license__ = "GPLv3"
    __authors__ = [("reissdorf", "reissdorf@domain.invalid")]

    prefered_hosters = None
    ignored_hosters = None

    HOSTS_LOOKUP_PATTERN = r'\/download\/gethosts\/[a-z0-9]+\/[A-Za-z0-9._-]+'
    LINK_PATTERN = r'>(http://go4up.com/rd/[a-z0-9]+/\d+)<'
    BASE_URL = 'http://go4up.com'

    def decrypt(self, pyfile):

        self.html = self.load(pyfile.url, decode=True)
        package_links = []
        self.prefered_hosters = self.getConfig("preferedHoster").split('|')
        self.ignored_hosters = self.getConfig("ignoredHoster").split('|')

        package_name, folder_name = self.getPackageNameAndFolder()

        hosts_url = re.search(self.HOSTS_LOOKUP_PATTERN, self.html)
        self.html = self.load(self.BASE_URL + hosts_url.group(0), decode=True)

        hosts_links = re.findall(self.LINK_PATTERN, self.html)

        for link in hosts_links:
            found_package_links = self.find_package_links(link)
            if len(found_package_links) > 0:
                package_links = package_links + found_package_links

        self.logDebug("Package has %d links" % len(package_links))

        if len(package_links) > 0:
            package_links.sort(key=lambda x: urlparse(link).hostname in self.prefered_hosters)
            self.packages = [(package_name, package_links, folder_name)]
        else:
            self.fail('Could not extract any links')


    def find_package_links(self, url):
        html = self.load(url, decode=True)
        soup = BeautifulSoup(html)
        container = soup.find('div', {'id': 'linklist'})
        links = container.find('a')
        package_links = []
        for link in links:
            hostname = urlparse(link).hostname
            if hostname not in self.ignored_hosters:
                package_links.append(link)
        return package_links
