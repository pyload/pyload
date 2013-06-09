# -*- coding: utf-8 -*-

import re
from module.plugins.Crypter import Crypter
from module.network.HTTPRequest import BadHeader

class EmbeduploadCom(Crypter):
    __name__ = "EmbeduploadCom"
    __type__ = "crypter"
    __pattern__ = r"http://(www\.)?embedupload.com/\?d=.*"
    __version__ = "0.02"
    __description__ = """EmbedUpload.com crypter"""
    __config__ = [("preferedHoster", "str", "Prefered hoster list (bar-separated) ", "embedupload"),
        ("ignoredHoster", "str", "Ignored hoster list (bar-separated) ", "")]
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    LINK_PATTERN = r'<div id="([^"]+)"[^>]*>\s*<a href="([^"]+)" target="_blank" (?:class="DownloadNow"|style="color:red")>'

    def decrypt(self, pyfile):
        self.html = self.load(self.pyfile.url, decode=True)
        tmp_links = [] 
        new_links = []
               
        found = re.findall(self.LINK_PATTERN, self.html)
        if found:
            prefered_set = set(self.getConfig("preferedHoster").split('|'))
            prefered_set = map(lambda s: s.lower().split('.')[0], prefered_set)
            print "PF", prefered_set
            tmp_links.extend([x[1] for x in found if x[0] in prefered_set])
            self.getLocation(tmp_links, new_links)

            if not new_links:
                ignored_set = set(self.getConfig("ignoredHoster").split('|'))
                ignored_set = map(lambda s: s.lower().split('.')[0], ignored_set)
                print "IG", ignored_set 
                tmp_links.extend([x[1] for x in found if x[0] not in ignored_set])                
                self.getLocation(tmp_links, new_links)

        if new_links:
            self.core.files.addLinks(new_links, self.pyfile.package().id)
        else:
            self.fail('Could not extract any links')
            
    def getLocation(self, tmp_links, new_links):
        for link in tmp_links:
            try:
                header = self.load(link, just_header = True)
                if "location" in header: 
                    new_links.append(header['location'])
            except BadHeader:
                pass
            
        