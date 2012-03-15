# -*- coding: utf-8 -*-

from module.network.RequestFactory import getURL
from module.plugins.internal.MultiHoster import MultiHoster

class ZeveraCom(MultiHoster):
    __name__ = "ZeveraCom"
    __version__ = "0.01"
    __type__ = "hook"
    __config__ = [("activated", "bool", "Activated", "False"),
                  ("hosterListMode", "all;listed;unlisted", "Use for hosters (if supported)", "all"),
                  ("hosterList", "str", "Hoster list (comma separated)", "")]
    __description__ = """Real-Debrid.com hook plugin"""
    __author_name__ = ("Devirex, Hazzard")
    __author_mail__ = ("naibaf_11@yahoo.de")

    replacements = [("freakshare.net", "freakshare.com"), ("2shared.com", "twoshared.com"), ("4shared.com", "fourshared.com"),
                    ("easy-share.com", "crocko.com"), ("hellshare.com", "hellshare.cz")]

    def getHoster(self):
        page = getURL("http://www.zevera.com/jDownloader.ashx?cmd=gethosters")        
        hosters = set([x.strip() for x in page.replace("\"", "").split(",")])   
        
        configMode = self.getConfig('hosterListMode')
        if configMode in ("listed", "unlisted"):
            configList = set(self.getConfig('hosterList').strip().lower().replace('|',',').replace(';',',').split(','))
            configList.discard(u'')
            if configMode == "listed":
                hosters &= configList
            else:
                hosters -= configList
        
        return list(hosters)                                