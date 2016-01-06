# -*- coding: utf-8 -*-

import re,urlparse

from module.plugins.internal.SimpleCrypter import SimpleCrypter
from module.plugins.internal.SimpleHoster import parse_fileInfo

class MovieblogOrg(SimpleCrypter):
    __name__ = "MovieblogOrg"
    __type__ = "crypter"
    __version__ = "0.10"
    __pattern__ = r'https?://(www\.)?(movie-blog|hd-world).org/\d{0,4}/\d{0,2}/\d{0,2}/.+'
    __description__ = """movie-blog.org/hd-world.org decrypter plugin"""
    __config__ = [("hosters", "str", "Hosters to use, eg. OboomCom (separated by comma)", "all"),
                  ("hostersInParallel", "1;2;3;4;5;all", "How many hosters from above to use in parallel", "all"),
                  ("readPackageName", "bool", "Search package/folder name on the website", "True")]
    __authors__ = [("zapp-brannigan", "")]

    NAME_PATTERN = r'title="Permanent Link: (?P<N>.+)">( <span class="item">|.*</a></h2>)'
    LINK_PATTERN = r'<strong>(Download|Mirror).*href="(?P<LINK>[\w\d\/\.\:\_\-]*)"\s*( target=.?_blank.?)?>(?P<HOSTER>.+)</a>'      

    def decrypt(self,pyfile):
        self.html = self.load(pyfile.url)
        self.getFileInfo()
        self.links = self.getLinks()
               
        if self.links:
            name = folder = pyfile.name
            self.packages.append((name, self.links, folder))
        else:
            self.fail("No links found - Plungin out of date?")
        
    
    def setPackagePassword(self):
        if "movie-blog" in self.pyfile.url:
            self.pyfile.package().password = "movie-blog.org"
        else:
            self.pyfile.package().password = "hd-world.org"
             
    def getFileInfo(self):
        self.check_info()
        self.setPackagePassword()
        name, size, status, url = parse_fileInfo(self)
        
        if not self.get_config("readPackageName"):
            self.pyfile.name = self.info['name'] = self.info['folder'] = self.pyfile.package().name
            return self.info

        self.info['folder'] = self.pyfile.name

        self.log_debug("FILE NAME: %s" % self.pyfile.name)
        return self.info
        
    def searchLinks(self):
        found = re.findall(self.LINK_PATTERN,self.html)
        links = {}
        fav_links = []
        count = self.get_config("hostersInParallel")
        
        if count == "all":
            count = None
            self.log_info("Will use all whitelisted hosters")
        else:
            count = int(count)
            self.log_info("Will use %s hoster(s) from the whitelist" %str(count))
        
        if found:
            self.log_debug("All available links: %s" %found)
            for i in found:
                if re.match(self.HOSTERS.lower(),i[3].lower().replace(".","").replace("-","").replace(" ","")):
                    self.log_info("Found links for %s" %i[3])
                    links[i[3].lower().replace(".","").replace("-","").replace(" ","")] = i[1]
        else:
            self.error("No links found")
    
        for hoster in self.HOSTERS.lower().split("|"):
            if links.has_key(hoster):
                fav_links.append(links[hoster])
               
        if self.HOSTERS == ".*":
            fav_links = links.values()
            
        self.log_debug("All usable links: %s" %links)
        self.log_debug("Favourite links: %s" %fav_links)
        
        return fav_links[0:count]
    
    def getLinks(self):
        self.setPackagePassword()
        hosters = self.get_config("hosters")
        
        if hosters == "all" or hosters == "":
            self.HOSTERS = r'.*'
            self.log_info("Whitelisted hoster(s): all")
        else:
            self.HOSTERS = hosters.replace(",","|").replace(" ","").replace(";","|").replace("-","").replace(".","")
            self.log_info("Whitelisted hoster(s): %s" %self.HOSTERS)
            
        links = self.searchLinks()
        
        if len(links) == 0:
            self.fail("No suitable hoster found")
            
        self.log_debug("Final links: %s" %links)

        return links