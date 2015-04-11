# -*- coding: utf-8 -*

import re
import HTMLParser

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class LolabitsEs(SimpleHoster):
    __name__    = "LolabitsEs"
    __type__    = "hoster"
    __version__ = "0.01"

    __pattern__ = r'https?://(?:www\.)?lolabits.es/.*'

    __description__ = """lolabits.es hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zapp-brannigan", "fuerst.reinje@web.de")]


    NAME_PATTERN    = r'Descargar: <b>(?P<N>.+?)</b>'
    SIZE_PATTERN    = r'class="fileSize">(?P<S>[\d.,]+) (?P<U>[\w^_]+)<'
    
    OFFLINE_PATTERN = r'Un usuario con este nombre no existe'


    def setup(self):
        self.chunkLimit = 1

    def handleFree(self, pyfile):
        fileid = re.search(r'name="FileId" value="(\d+)"',self.html).group(1)
        self.logDebug("FileID: %s" %fileid)
        
        token = re.search(r'name="__RequestVerificationToken" type="hidden" value="(.+?)"',self.html).group(1)
        self.logDebug("Token: %s" %token)
        
        self.html = self.load("http://lolabits.es/action/License/Download",
                              cookies = True,
                              post    = {"fileId"                     : fileid,
                                         "__RequestVerificationToken" : token}
                             ).decode('unicode-escape')
        m = re.search(r'"redirectUrl":"(.+?)"',self.html)
        self.link = HTMLParser.HTMLParser().unescape(m.group(1))
        
        
getInfo = create_getInfo(LolabitsEs)
