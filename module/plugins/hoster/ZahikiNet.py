# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class ZahikiNet(SimpleHoster):
    __name__    = "ZahikiNet"
    __type__    = "hoster"
    __version__ = "0.02"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?zahiki\.net/\w+/.+'

    __description__ = """Zahiki.net hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    DIRECT_LINK = True

    NAME_PATTERN    = r'/(?P<N>.+?) </title>'
    OFFLINE_PATTERN = r'>(Not Found|Il file selezionato non esiste)'

    LINK_FREE_PATTERN = r'file: "(.+?)"'


    def setup(self):
        self.resume_download = True
        self.multiDL = True
        self.limitDL = 6


getInfo = create_getInfo(ZahikiNet)
