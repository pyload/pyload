# -*- coding: utf-8 -*

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo
from module.utils import html_unescape


class LolabitsEs(SimpleHoster):
    __name__    = "LolabitsEs"
    __type__    = "hoster"
    __version__ = "0.03"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?lolabits\.es/.+'

    __description__ = """Lolabits.es hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zapp-brannigan", "fuerst.reinje@web.de")]


    NAME_PATTERN    = r'Descargar: <b>(?P<N>.+?)<'
    SIZE_PATTERN    = r'class="fileSize">(?P<S>[\d.,]+) (?P<U>[\w^_]+)'
    OFFLINE_PATTERN = r'Un usuario con este nombre no existe'

    FILEID_PATTERN = r'name="FileId" value="(\d+)"'
    TOKEN_PATTERN  = r'name="__RequestVerificationToken" type="hidden" value="(.+?)"'
    LINK_PATTERN   = r'"redirectUrl":"(.+?)"'


    def setup(self):
        self.chunk_limit = 1


    def handle_free(self, pyfile):
        fileid = re.search(self.FILEID_PATTERN, self.html).group(1)
        self.log_debug("FileID: " + fileid)

        token = re.search(self.TOKEN_PATTERN, self.html).group(1)
        self.log_debug("Token: " + token)

        self.html = self.load("http://lolabits.es/action/License/Download",
                              post={'fileId'                     : fileid,
                                    '__RequestVerificationToken' : token},
                              decode="unicode-escape")

        self.link = html_unescape(re.search(self.LINK_PATTERN, self.html).group(1))


getInfo = create_getInfo(LolabitsEs)
