# -*- coding: utf-8 -*-

import re
from module.plugins.Crypter import Crypter

class FilebeerInfoFolder(Crypter):
    __name__ = "FilebeerInfoFolder"
    __type__ = "crypter"
    __pattern__ = r"http://(?:www\.)?filebeer\.info/(\d+~f).*"
    __version__ = "0.01"
    __description__ = """Filebeer.info Folder Plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    LINK_PATTERN = r'<td title="[^"]*"><a href="([^"]+)" target="_blank">'
    PAGE_COUNT_PATTERN = r'<p class="introText">\s*Total Pages (\d+)'
    
    def decrypt(self, pyfile):        
        pyfile.url = re.sub(self.__pattern__, r'http://filebeer.info/\1?page=1', pyfile.url)        
        html = self.load(pyfile.url)
        
        page_count = int(re.search(self.PAGE_COUNT_PATTERN, html).group(1))
        new_links = []
                
        for i in range(1, page_count + 1):            
            self.logInfo("Fetching links from page %i" % i)                
            new_links.extend(re.findall(self.LINK_PATTERN, html))
                        
            if i < page_count:
                html = self.load("%s?page=%d" % (pyfile.url, i+1))

        if new_links:
            self.core.files.addLinks(new_links, self.pyfile.package().id)
        else:
            self.fail('Could not extract any links')