# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class GamefrontCom(SimpleHoster):
    __name__    = "GamefrontCom"
    __type__    = "hoster"
    __version__ = "0.08"

    __pattern__ = r'http://(?:www\.)?gamefront\.com/files/(?P<ID>\d+)'

    __description__ = """Gamefront.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    NAME_PATTERN    = r'<title>(?P<N>.+?) \| Game Front</title>'
    SIZE_PATTERN    = r'>File Size:</dt>\s*<dd>(?P<S>[\d.,]+) (?P<U>[\w^_]+)'
    OFFLINE_PATTERN = r'<p>File not found'

    LINK_FREE_PATTERN = r"downloadUrl = '(.+?)'"


    def setup(self):
        self.resumeDownload = True
        self.multiDL        = True


    def handleFree(self, pyfile):
        self.html = self.load("http://www.gamefront.com/files/service/thankyou",
                              get={'id': self.info['pattern']['ID']})
        return super(GamefrontCom, self).handleFree(pyfile)


getInfo = create_getInfo(GamefrontCom)
