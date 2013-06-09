# -*- coding: utf-8 -*-

import re
from module.plugins.Crypter import Crypter
from module.common.json_layer import json_loads
from time import time

class MultiuploadCom(Crypter):
    __name__ = "MultiuploadCom"
    __type__ = "crypter"
    __pattern__ = r"http://(?:www\.)?multiupload.com/(\w+)"
    __version__ = "0.01"
    __description__ = """MultiUpload.com crypter"""
    __config__ = [("preferedHoster", "str", "Prefered hoster list (bar-separated) ", "multiupload"),
        ("ignoredHoster", "str", "Ignored hoster list (bar-separated) ", "")]
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    ML_LINK_PATTERN = r'<div id="downloadbutton_" style=""><a href="([^"]+)"'

    def decrypt(self, pyfile):
        self.html = self.load(pyfile.url)
        found = re.search(self.ML_LINK_PATTERN, self.html)
        ml_url = found.group(1) if found else None
        
        json_list = json_loads(self.load("http://multiupload.com/progress/", get = {
            "d": re.search(self.__pattern__, pyfile.url).group(1),
            "r": str(int(time()*1000))        
            }))
        new_links = []
               
        prefered_set = map(lambda s: s.lower().split('.')[0], set(self.getConfig("preferedHoster").split('|')))       
        
        if ml_url and 'multiupload' in prefered_set: new_links.append(ml_url)               
        
        for link in json_list:          
            if link['service'].lower() in prefered_set and int(link['status']) and not int(link['deleted']):
                url = self.getLocation(link['url'])
                if url: new_links.append(url)        

        if not new_links:                    
            ignored_set = map(lambda s: s.lower().split('.')[0], set(self.getConfig("ignoredHoster").split('|')))
            
            if 'multiupload' not in ignored_set: new_links.append(ml_url)                   
        
            for link in json_list:         
                if link['service'].lower() not in ignored_set and int(link['status']) and not int(link['deleted']):
                    url = self.getLocation(link['url'])
                    if url: new_links.append(url)

        if new_links:
            self.core.files.addLinks(new_links, self.pyfile.package().id)
        else:
            self.fail('Could not extract any links')
            
    def getLocation(self, url):
        header = self.load(url, just_header = True)
        return header['location'] if "location" in header else None     