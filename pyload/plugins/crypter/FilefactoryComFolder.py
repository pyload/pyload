# -*- coding: utf-8 -*-

import re
from module.plugins.Crypter import Crypter

class FilefactoryComFolder(Crypter):
    __name__ = "FilefactoryComFolder"
    __type__ = "crypter"
    __pattern__ = r"(http://(www\.)?filefactory\.com/f/\w+).*"
    __version__ = "0.1"
    __description__ = """Filefactory.com Folder Plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    FOLDER_PATTERN = r'<table class="items" cellspacing="0" cellpadding="0">(.*?)</table>'
    LINK_PATTERN = r'<td class="name"><a href="([^"]+)">'
    PAGINATOR_PATTERN = r'<div class="list">\s*<label>Pages</label>\s*<ul>(.*?)</ul>\s*</div>'
    NEXT_PAGE_PATTERN = r'<li class="current">.*?</li>\s*<li class=""><a href="([^"]+)">'

    def decrypt(self, pyfile):
        url_base = re.search(self.__pattern__, self.pyfile.url).group(1)
        html = self.load(url_base)

        new_links = []
        for i in range(1,100):
            self.logInfo("Fetching links from page %i" % i)
            found = re.search(self.FOLDER_PATTERN, html, re.DOTALL)
            if found is None: self.fail("Parse error (FOLDER)")

            new_links.extend(re.findall(self.LINK_PATTERN, found.group(1)))

            try:
                paginator = re.search(self.PAGINATOR_PATTERN, html, re.DOTALL).group(1)
                next_page = re.search(self.NEXT_PAGE_PATTERN, paginator).group(1)
                html = self.load("%s/%s" % (url_base, next_page))
            except Exception, e:
                break
        else:
            self.logInfo("Limit of 99 pages reached, aborting")

        if new_links:
            self.core.files.addLinks(new_links, self.pyfile.package().id)
        else:
            self.fail('Could not extract any links')