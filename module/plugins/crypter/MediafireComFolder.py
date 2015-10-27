# -*- coding: utf-8 -*-

import re

from module.plugins.internal.Crypter import Crypter, create_getInfo
from module.plugins.internal.utils import json


class MediafireComFolder(Crypter):
    __name__    = "MediafireComFolder"
    __type__    = "crypter"
    __version__ = "0.20"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?mediafire\.com/(folder/|\?sharekey=|\?\w{13}($|[/#]))'
    __config__  = [("activated"            , "bool", "Activated"                          , True),
                   ("use_premium"          , "bool", "Use premium account if available"   , True),
                   ("use_subfolder"        , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description__ = """Mediafire.com folder decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    FOLDER_KEY_PATTERN = r'var afI= \'(\w+)'
    LINK_PATTERN = r'<meta property="og:url" content="http://www\.mediafire\.com/\?(\w+)"/>'


    def _get_url(url):
        try:
            for _i in xrange(3):
                header = self.load(url, just_header=True)

                for line in header.splitlines():
                    line = line.lower()

                    if 'location' in line:
                        url = line.split(':', 1)[1].strip()
                        if 'error.php?errno=320' in url:
                            return url, 1

                        elif not url.startswith('http://'):
                            url = 'http://www.mediafire.com' + url

                        break

                    elif 'content-disposition' in line:
                        return url, 2

        except Exception:
            return url, 3

        else:
            return url, 0


    def decrypt(self, pyfile):
        url, result = self._get_url(pyfile.url)
        self.log_debug("Location (%d): %s" % (result, url))

        if result is 0:
            #: Load and parse html
            html = self.load(pyfile.url)
            m = re.search(self.LINK_PATTERN, html)
            if m is not None:
                #: File page
                self.links.append("http://www.mediafire.com/file/%s" % m.group(1))
            else:
                #: Folder page
                m = re.search(self.FOLDER_KEY_PATTERN, html)
                if m is not None:
                    folder_key = m.group(1)
                    self.log_debug("FOLDER KEY: %s" % folder_key)

                    json_resp = json.loads(self.load("http://www.mediafire.com/api/folder/get_info.php",
                                                     get={'folder_key'     : folder_key,
                                                          'response_format': "json",
                                                          'version'        : 1}))
                    # self.log_info(json_resp)
                    if json_resp['response']['result'] == "Success":
                        for link in json_resp['response']['folder_info']['files']:
                            self.links.append("http://www.mediafire.com/file/%s" % link['quickkey'])
                    else:
                        self.fail(json_resp['response']['message'])

        elif result is 1:
            self.offline()

        else:
            self.links.append(url)


getInfo = create_getInfo(MediafireComFolder)
