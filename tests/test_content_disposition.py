# -*- coding: utf-8 -*-

import unittest
import re
from urllib2 import unquote

def get_filename_from_content_disposition(header):
    """Parse request header to retrieve filename from content disposition"""
    for orgline in header.splitlines():

        if orgline.startswith("Content-Disposition"):
            filename = ''
            if "filename=" in orgline:
                m = re.match(r".*filename=\"(.*)\"", orgline)
                filename = m.group(1)
            if "filename*=" in orgline:
                m = re.match(r".*filename\*=UTF-8''(.*)", orgline)
                filename = unquote(m.group(1))
            #split for directory traversal
            return filename.split('/')[-1].lower()

HEADER_SIMPLE = """HTTP/1.1 200 OK
Server: nginx
Date: Thu, 09 Apr 2015 13:15:41 GMT
Content-Type: application/octet-stream
Content-Length: 1228800
Last-Modified: Fri, 06 Feb 2015 10:50:42 GMT
Connection: close
Set-Cookie: SID=omaaeuvag5erb4vi2g3urlut41; path=/; domain=.sendspace.com
Expires: Thu, 19 Nov 1981 08:52:00 GMT
Cache-Control: no-store, no-cache, must-revalidate, post-check=0, pre-check=0
Content-Disposition: attachment;filename="NaiveFile.txt"
ETag: "54d49c82-12c000"
Accept-Ranges: bytes
"""

HEADER_UTF8 = """HTTP/1.1 200 OK
Server: nginx
Date: Thu, 09 Apr 2015 13:15:41 GMT
Content-Type: application/octet-stream
Content-Length: 1228800
Last-Modified: Fri, 06 Feb 2015 10:50:42 GMT
Connection: close
Set-Cookie: SID=omaaeuvag5erb4vi2g3urlut41; path=/; domain=.sendspace.com
Expires: Thu, 19 Nov 1981 08:52:00 GMT
Cache-Control: no-store, no-cache, must-revalidate, post-check=0, pre-check=0
Content-Disposition: attachment;filename*=UTF-8''Na%C3%AFveFile.txt
ETag: "54d49c82-12c000"
Accept-Ranges: bytes
"""

HEADER_TRAVERSAL = """HTTP/1.1 200 OK
Server: nginx
Date: Thu, 09 Apr 2015 13:15:41 GMT
Content-Type: application/octet-stream
Content-Length: 1228800
Last-Modified: Fri, 06 Feb 2015 10:50:42 GMT
Connection: close
Set-Cookie: SID=omaaeuvag5erb4vi2g3urlut41; path=/; domain=.sendspace.com
Expires: Thu, 19 Nov 1981 08:52:00 GMT
Cache-Control: no-store, no-cache, must-revalidate, post-check=0, pre-check=0
Content-Disposition: attachment;filename="../../NaiveFile.txt"
ETag: "54d49c82-12c000"
Accept-Ranges: bytes
"""


class ContentDispositionTests(unittest.TestCase):
    """Test Content Disposition Headers to get filename"""

    def test_header_simple(self):
        """We expect naivefile.txt"""
        filename = get_filename_from_content_disposition(HEADER_SIMPLE)
        self.assertEqual(filename, 'naivefile.txt')

    def test_header_utf8(self):
        """We expect na\xc3\xafvefile.txt"""
        filename = get_filename_from_content_disposition(HEADER_UTF8)
        self.assertEqual(filename, 'na\xc3\xafvefile.txt')

    def test_header_traversal(self):
        """We expect naivefile.txt"""
        filename = get_filename_from_content_disposition(HEADER_TRAVERSAL)
        self.assertEqual(filename, 'naivefile.txt')

if __name__ == '__main__':
    unittest.main()
