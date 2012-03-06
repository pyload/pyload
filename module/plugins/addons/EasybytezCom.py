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
    __version__ = "0.01"
    __type__ = "hook"
    __config__ = [("activated", "bool", "Activated", "False"),
        ("includeHoster", "str", "Use only for downloads from (comma-separated hosters)", ""),
        ("excludeHoster", "str", "Do not use for downloads from (comma-separated hosters)", "")]
    __description__ = """EasyBytez.com hook plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    def getHoster(self):

        hoster = set(['2shared.com', 'easy-share.com', 'filefactory.com', 'fileserve.com', 'filesonic.com', 'hotfile.com', 'mediafire.com', 'megaupload.com', 'netload.in', 'rapidshare.com', 'uploading.com', 'wupload.com', 'oron.com', 'uploadstation.com', 'ul.to', 'uploaded.to'])   
        
        option = self.getConfig('includeHoster').strip()
        if option: hoster &= getConfigSet(option)
        option = self.getConfig('excludeHoster').strip()
        if option: hoster -= getConfigSet(option)
        
        return list(hoster)