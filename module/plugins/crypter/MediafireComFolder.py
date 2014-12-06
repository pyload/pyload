# -*- coding: utf-8 -*-

import re
from module.plugins.Crypter import Crypter
from module.plugins.hoster.MediafireCom import checkHTMLHeader
from module.common.json_layer import json_loads


class MediafireComFolder(Crypter):
    __name__    = "MediafireComFolder"
    __type__    = "crypter"
    __version__ = "0.14"

    __pattern__ = r'http://(?:www\.)?mediafire\.com/(folder/|\?sharekey=|\?\w{13}($|[/#]))'
    __config__  = [("use_subfolder", "bool", "Save package to subfolder", True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description__ = """Mediafire.com folder decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    FOLDER_KEY_PATTERN = r'var afI= \'(\w+)'
    LINK_PATTERN = r'<meta property="og:url" content="http://www\.mediafire\.com/\?(\w+)"/>'


    def decrypt(self, pyfile):
        url, result = checkHTMLHeader(pyfile.url)
        self.logDebug("Location (%d): %s" % (result, url))

        if result == 0:
            # load and parse html
            html = self.load(pyfile.url)
            m = re.search(self.LINK_PATTERN, html)
            if m:
                # file page
                self.urls.append("http://www.mediafire.com/file/%s" % m.group(1))
            else:
                # folder page
                m = re.search(self.FOLDER_KEY_PATTERN, html)
                if m:
                    folder_key = m.group(1)
                    self.logDebug("FOLDER KEY: %s" % folder_key)

                    json_resp = json_loads(self.load("http://www.mediafire.com/api/folder/get_info.php",
                                                     get={'folder_key'     : folder_key,
                                                          'response_format': "json",
                                                          'version'        : 1}))
                    #self.logInfo(json_resp)
                    if json_resp['response']['result'] == "Success":
                        for link in json_resp['response']['folder_info']['files']:
                            self.urls.append("http://www.mediafire.com/file/%s" % link['quickkey'])
                    else:
                        self.fail(json_resp['response']['message'])
        elif result == 1:
            self.offline()
        else:
            self.urls.append(url)
