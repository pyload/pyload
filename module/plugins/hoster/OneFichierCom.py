# -*- coding: utf-8 -*-

import re
import urllib2

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class OneFichierCom(SimpleHoster):
    __name__    = "OneFichierCom"
    __type__    = "hoster"
    __version__ = "0.81"

    __pattern__ = r'https?://(?:www\.)?(?:(?P<ID1>\w+)\.)?(?P<HOST>1fichier\.com|alterupload\.com|cjoint\.net|d(es)?fichiers\.com|dl4free\.com|megadl\.fr|mesfichiers\.org|piecejointe\.net|pjointe\.com|tenvoi\.com)(?:/\?(?P<ID2>\w+))?'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """1fichier.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("fragonib", "fragonib[AT]yahoo[DOT]es"),
                       ("the-razer", "daniel_ AT gmx DOT net"),
                       ("zoidberg", "zoidberg@mujmail.cz"),
                       ("imclem", None),
                       ("stickell", "l.stickell@yahoo.it"),
                       ("Elrick69", "elrick69[AT]rocketmail[DOT]com"),
                       ("Walter Purcaro", "vuolter@gmail.com"),
                       ("Ludovic Lehmann", "ludo.lehmann@gmail.com")]


    NAME_PATTERN = r'>FileName :</td>\s*<td.*>(?P<N>.+?)<'
    SIZE_PATTERN = r'>Size :</td>\s*<td.*>(?P<S>[\d.,]+) (?P<U>[\w^_]+)'

    OFFLINE_PATTERN = r'File not found !\s*<'

    COOKIES     = [("1fichier.com", "LG", "en")]
    DISPOSITION = False  #: Remove in 0.4.10

    WAIT_PATTERN = r'>You must wait \d+ minutes'


    def setup(self):
        self.multiDL        = self.premium
        self.resumeDownload = True


    #@NOTE: Temp work-around to `Content-Disposition=filename*=UTF-8` bug!
    def handleDirect(self, pyfile):
        self.link = self.directLink(pyfile.url, self.resumeDownload)

        if self.link:
            remote = urllib2.urlopen(self.link)
            name   = remote.info()['Content-Disposition'].split(';')
            pyfile.name = name[1].split('filename=')[1][1:]


    def handleFree(self, pyfile):
        id = self.info['pattern']['ID1'] or self.info['pattern']['ID2']
        url, inputs = self.parseHtmlForm('action="https://1fichier.com/\?%s' % id)

        if not url:
            self.fail(_("Download link not found"))

        if "pass" in inputs:
            inputs['pass'] = self.getPassword()

        inputs['submit'] = "Download"

        self.download(url, post=inputs)


    def handlePremium(self, pyfile):
        self.download(pyfile.url, post={'dl': "Download", 'did': 0})


getInfo = create_getInfo(OneFichierCom)
