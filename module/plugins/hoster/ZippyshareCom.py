#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo

class ZippyshareCom(SimpleHoster):
    __name__ = "ZippyshareCom"
    __type__ = "hoster"
    __pattern__ = r"(http://www\d{0,2}\.zippyshare.com)/v(?:/|iew.jsp.*key=)(\d+)"
    __version__ = "0.31"
    __description__ = """Zippyshare.com Download Hoster"""
    __author_name__ = ("spoob", "zoidberg")
    __author_mail__ = ("spoob@pyload.org", "zoidberg@mujmail.cz")
    
    FILE_NAME_PATTERN = r'>Name:</font>\s*<font [^>]*>(?P<N>[^<]+)</font><br />'
    FILE_SIZE_PATTERN = r'>Size:</font>\s*<font [^>]*>(?P<S>[0-9.,]+) (?P<U>[kKMG]+)i?B</font><br />'
    FILE_OFFLINE_PATTERN = r'>File does not exist on this server</div>'

    DOWNLOAD_URL_PATTERN = r"document\.getElementById\('dlbutton'\).href = ([^;]+);"
    SEED_PATTERN = r"seed: (\d*)"

    def setup(self):
        self.html = None
        self.wantReconnect = False
        self.multiDL = True

    def handleFree(self):
        url = self.get_file_url()
        self.logDebug("Download URL %s" % url)
        self.download(url, cookies = True)
        
    def get_file_url(self):
        """ returns the absolute downloadable filepath
        """
        file_host, file_key = re.search(self.__pattern__, self.pyfile.url).groups()

        found = re.search(self.DOWNLOAD_URL_PATTERN, self.html)
        if found:
            url = self.js.eval(found.group(1))
        else:
            seed_search = re.search(self.SEED_PATTERN, self.html)
            if seed_search is None: self.parseError('SEED')           
            
            file_seed = int(seed_search.group(1))
            time = str((file_seed * 24) % 6743256)   
            url = "/download?key=" + str(file_key) + "&time=" + str(time)
        
        return file_host + url

getInfo = create_getInfo(ZippyshareCom)