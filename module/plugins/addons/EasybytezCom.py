# -*- coding: utf-8 -*-

from module.network.RequestFactory import getURL
from module.plugins.internal.MultiHoster import MultiHoster
import re

def getConfigSet(option):
    s = set(option.lower().replace(',','|').split('|'))
    s.discard(u'')
    return s

class EasybytezCom(MultiHoster):
    __name__ = "EasybytezCom"
    __version__ = "0.02"
    __type__ = "hook"
    __config__ = [("activated", "bool", "Activated", "False"),
                  ("hosterListMode", "all;listed;unlisted", "Use for hosters (if supported)", "all"),
                  ("hosterList", "str", "Hoster list (comma separated)", "")]
    __description__ = """EasyBytez.com hook plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    def getHoster(self):

        hoster = set(['2shared.com', 'easy-share.com', 'filefactory.com', 'fileserve.com', 'filesonic.com', 'hotfile.com', 'mediafire.com', 'megaupload.com', 'netload.in', 'rapidshare.com', 'uploading.com', 'wupload.com', 'oron.com', 'uploadstation.com', 'ul.to', 'uploaded.to'])   
        
        configMode = self.getConfig('hosterListMode')
        if configMode in ("listed", "unlisted"):
            configList = set(self.getConfig('hosterList').strip().lower().replace('|',',').replace(';',',').split(','))
            configList.discard(u'')
            if configMode == "listed":
                hoster &= configList
            else:
                hoster -= configList
        
        return list(hoster)