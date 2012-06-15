# -*- coding: utf-8 -*-

import re
from module.plugins.Crypter import Crypter
from module.plugins.hoster.MediafireCom import checkHTMLHeader
from module.common.json_layer import json_loads

class MediafireComFolder(Crypter):
    __name__ = "MediafireComFolder"
    __type__ = "crypter"
    __pattern__ = r"http://(\w*\.)*mediafire\.com/(folder/|\?sharekey=|\?\w{13}($|[/#]))"
    __version__ = "0.14"
    __description__ = """Mediafire.com Folder Plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    FOLDER_KEY_PATTERN = r"var afI= '(\w+)';"
    FILE_URL_PATTERN = '<meta property="og:url" content="http://www.mediafire.com/\?(\w+)"/>'

    def decrypt(self, pyfile):
        new_links = []
        
        url, result = checkHTMLHeader(pyfile.url)
        self.logDebug('Location (%d): %s' % (result, url))
            
        if result == 0:
            # load and parse html            
            html = self.load(pyfile.url)
            found = re.search(self.FILE_URL_PATTERN, html)
            if found:
                # file page
                new_links.append("http://www.mediafire.com/file/%s" % found.group(1))
            else:
                # folder page
                found = re.search(self.FOLDER_KEY_PATTERN, html)
                if found:                               
                    folder_key = found.group(1)
                    self.logDebug("FOLDER KEY: %s" % folder_key)
                    
                    json_resp = json_loads(self.load("http://www.mediafire.com/api/folder/get_info.php?folder_key=%s&response_format=json&version=1" % folder_key))
                    #self.logInfo(json_resp)
                    if json_resp['response']['result'] == "Success":
                        for link in json_resp['response']['folder_info']['files']:
                            new_links.append("http://www.mediafire.com/file/%s" % link['quickkey'])            
                    else:
                        self.fail(json_resp['response']['message'])
        elif result == 1:
            self.offline()             
        else:
            new_links.append(url)
    
        if new_links:
            self.core.files.addLinks(new_links, self.pyfile.package().id)
        else:
            self.fail('Could not extract any links')