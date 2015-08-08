# -*- coding: utf-8 -*-

import re
from module.plugins.internal.Crypter import Crypter
from module.plugins.hoster.MediafireCom import checkHTMLHeader
from module.common.json_layer import json_loads


class MediafireComFolder(Crypter):
    __name__    = "MediafireComFolder"
    __type__    = "crypter"
    __version__ = "0.16"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?mediafire\.com/(folder/|\?sharekey=|\?\w{13}($|[/#]))'
    __config__  = [("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description__ = """Mediafire.com folder decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    FOLDER_KEY_PATTERN = r'var afI= \'(\w+)'
    LINK_PATTERN = r'<meta property="og:url" content="http://www\.mediafire\.com/\?(\w+)"/>'


    def decrypt(self, pyfile):
        url, result = checkHTMLHeader(pyfile.url)
        self.log_debug("Location (%d): %s" % (result, url))

        if result == 0:
            #: Load and parse html
            html = self.load(pyfile.url)
            m = re.search(self.LINK_PATTERN, html)
            if m:
                #: File page
                self.urls.append("http://www.mediafire.com/file/%s" % m.group(1))
            else:
                #: Folder page
                m = re.search(self.FOLDER_KEY_PATTERN, html)
                if m:
                    folder_key = m.group(1)
                    self.log_debug("FOLDER KEY: %s" % folder_key)

                    json_resp = json_loads(self.load("http://www.mediafire.com/api/folder/get_info.php",
                                                     get={'folder_key'     : folder_key,
                                                          'response_format': "json",
                                                          'version'        : 1}))
                    # self.log_info(json_resp)
                    if json_resp['response']['result'] == "Success":
                        for link in json_resp['response']['folder_info']['files']:
                            self.urls.append("http://www.mediafire.com/file/%s" % link['quickkey'])
                    else:
                        self.fail(json_resp['response']['message'])
        elif result == 1:
            self.offline()
        else:
            self.urls.append(url)
