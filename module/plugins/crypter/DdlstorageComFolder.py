# -*- coding: utf-8 -*-

import re
from module.plugins.Crypter import Crypter
from module.plugins.hoster.MediafireCom import checkHTMLHeader
from module.common.json_layer import json_loads

class DdlstorageComFolder(Crypter):
    __name__ = "DdlstorageComFolder"
    __type__ = "crypter"
    __pattern__ = r"http://(?:\w*\.)*?ddlstorage.com/folder/\w{10}"
    __version__ = "0.01"
    __description__ = """DDLStorage.com Folder Plugin"""
    __author_name__ = ("godofdream")
    __author_mail__ = ("soilfiction@gmail.com")

    FILE_URL_PATTERN = '<a style="text-decoration:none;" href="http://www.ddlstorage.com/(.*)">'

    def decrypt(self, pyfile):
        new_links = []
        # load and parse html            
        html = self.load(pyfile.url)
        found = re.findall(self.FILE_URL_PATTERN, html)
        self.logDebug(found)
        for link in found:
            # file page
            new_links.append("http://www.ddlstorage.com/%s" % link)
    
        if new_links:
            self.core.files.addLinks(new_links, self.pyfile.package().id)
        else:
            self.fail('Could not extract any links')
