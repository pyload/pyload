# -*- coding: utf-8 -*-

from module.network.RequestFactory import getURL
from module.plugins.internal.MultiHoster import MultiHoster
import re

def getConfigSet(option):
    s = set(option.lower().split('|'))
    s.discard(u'')
    return s

class MultishareCz(MultiHoster):
    __name__ = "MultishareCz"
    __version__ = "0.01"
    __type__ = "hook"
    __config__ = [("activated", "bool", "Activated", "False"),
        ("includeHoster", "str", "Use only for downloads from (bar-separated hosters)", ""),
        ("excludeHoster", "str", "Do not use for downloads from (bar-separated hosters)", "rapidshare.com|uloz.to")]
    __description__ = """MultiShare.cz hook plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    #replacements = [("freakshare.net", "freakshare.com")]
    HOSTER_PATTERN = r'<img class="logo-shareserveru"[^>]*alt="([^"]+)"></td>\s*<td class="stav"><img src="/img/loga/ok.png" alt="OK">'

    def getHoster(self):

        page = getURL("http://www.multishare.cz/monitoring/")
        hoster = set(m.group(1).lower() for m in re.finditer(self.HOSTER_PATTERN, page)) 
        
        option = self.getConfig('includeHoster').strip()
        if option: hoster &= getConfigSet(option)
        option = self.getConfig('excludeHoster').strip()
        if option: hoster -= getConfigSet(option)
        
        return list(hoster)