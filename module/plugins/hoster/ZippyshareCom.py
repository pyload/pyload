# -*- coding: utf-8 -*-

# Test links (random.bin):
# http://www13.zippyshare.com/v/18665333/file.html

import re
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo, timestamp


class ZippyshareCom(SimpleHoster):
    __name__ = "ZippyshareCom"
    __type__ = "hoster"
    __pattern__ = r'(?P<HOST>http://www\d{0,2}\.zippyshare.com)/v(?:/|iew.jsp.*key=)(?P<KEY>\d+)'
    __version__ = "0.48"
    __description__ = """Zippyshare.com hoster plugin"""
    __author_name__ = ("spoob", "zoidberg", "stickell","skylab")
    __author_mail__ = ("spoob@pyload.org", "zoidberg@mujmail.cz", "l.stickell@yahoo.it","development@sky-lab.de")


    FILE_NAME_PATTERN = r'>Name:</font>\s*<font [^>]*>(?P<N>[^<]+)</font><br />'
    FILE_SIZE_PATTERN = r'>Size:</font>\s*<font [^>]*>(?P<S>[0-9.,]+) (?P<U>[kKMG]+)i?B</font><br />'
    FILE_INFO_PATTERN = r'document\.getElementById\(\'dlbutton\'\)\.href = "[^;]*/(?P<N>[^"]+)";'
    FILE_OFFLINE_PATTERN = r'>File does not exist on this server</div>'

    SH_COOKIES = [('zippyshare.com', 'ziplocale', 'en')]
    
    def setup(self):
        self.multiDL = True

    def handleFree(self):
        url = self.get_file_url()
        if not url:
            self.fail("Download URL not found.")
        self.logDebug("Download URL: %s" % url)
        self.download(url)

    def get_file_url(self):
        """returns the absolute downloadable filepath"""
        url_parts = re.search("(addthis:url=\"(http://www(\d+).zippyshare.com/v/(\d*)/file.html))", self.html)
        number = url_parts.group(4)
        check = re.search("<script type=\"text/javascript\">([^<]*?)(var a = (\d*);)", self.html)
        if check is not None:
            a = int(re.search("<script type=\"text/javascript\">([^<]*?)(var a = (\d*);)", self.html).group(3))
            k = int(re.search("<script type=\"text/javascript\">([^<]*?)(\d*%(\d*))", self.html).group(3))
            checksum = ((a + 3) % k) * ((a + 3) % 3) + 18
        else:
            # This might work but is insecure
            # checksum = eval(re.search("((\d*)\s\%\s(\d*)\s\+\s(\d*)\s\%\s(\d*))", self.html).group(0))
            
            a = int(re.search("((?P<a>\d*)\s\%\s(?P<b>\d*)\s\+\s(?P<c>\d*)\s\%\s(?P<k>\d*))", self.html).group("a"))
            b = int(re.search("((?P<a>\d*)\s\%\s(?P<b>\d*)\s\+\s(?P<c>\d*)\s\%\s(?P<k>\d*))", self.html).group("b"))
            c = int(re.search("((?P<a>\d*)\s\%\s(?P<b>\d*)\s\+\s(?P<c>\d*)\s\%\s(?P<k>\d*))", self.html).group("c"))
            k = int(re.search("((?P<a>\d*)\s\%\s(?P<b>\d*)\s\+\s(?P<c>\d*)\s\%\s(?P<k>\d*))", self.html).group("k"))
            if a == c:
                checksum = ((a%b)+(a%k)) 
            else:
                checksum = ((a%b)+(c%k))
                
        self.logInfo(checksum)
        
        filename = re.search(r'>Name:</font>\s*<font [^>]*>(?P<N>[^<]+)</font><br />', self.html).group('N')

        url = "/d/" + str(number) + "/" + str(checksum) + "/" + filename
        self.logInfo(self.file_info['HOST'] + url)
        return self.file_info['HOST'] + url


getInfo = create_getInfo(ZippyshareCom)
