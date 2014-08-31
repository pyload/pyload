# -*- coding: utf-8 -*-

import re
from module.plugins.Crypter import Crypter
from module.plugins.hoster.MediafireCom import checkHTMLHeader
from module.common.json_layer import json_loads


class MediafireComFolder(Crypter):
    __name__ = "MediafireComFolder"
    __type__ = "crypter"
    __version__ = "0.14"

    __pattern__ = r'http://(?:www\.)?mediafire\.com/(folder/|\?sharekey=|\?\w{13}($|[/#]))'

    __description__ = """Mediafire.com folder decrypter plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"

    FOLDER_KEY_PATTERN = r"var afI= '(\w+)';"
    FILE_URL_PATTERN = r'<meta property="og:url" content="http://www.mediafire.com/\?(\w+)"/>'


    def decrypt(self, pyfile):
        url, result = checkHTMLHeader(pyfile.url)
        self.logDebug('Location (%d): %s' % (result, url))

        if result == 0:
            # load and parse html
            html = self.load(pyfile.url)
            m = re.search(self.FILE_URL_PATTERN, html)
            if m:
                # file page
                self.urls.append("http://www.mediafire.com/file/%s" % m.group(1))
            else:
                # folder page
                m = re.search(self.FOLDER_KEY_PATTERN, html)
                if m:
                    folder_key = m.group(1)
                    self.logDebug("FOLDER KEY: %s" % folder_key)

                    json_resp = json_loads(self.load(
                        "http://www.mediafire.com/api/folder/get_info.php?folder_key=%s&response_format=json&version=1" % folder_key))
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

        if not self.urls:
            self.fail('Could not extract any links')
