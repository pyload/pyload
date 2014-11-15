# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class OneFichierCom(SimpleHoster):
    __name__    = "OneFichierCom"
    __type__    = "hoster"
    __version__ = "0.73"

    __pattern__ = r'https?://(?:www\.)?(?:(?P<ID1>\w+)\.)?(?P<HOST>1fichier\.com|alterupload\.com|cjoint\.net|d(es)?fichiers\.com|dl4free\.com|megadl\.fr|mesfichiers\.org|piecejointe\.net|pjointe\.com|tenvoi\.com)(?:/\?(?P<ID2>\w+))?'

    __description__ = """1fichier.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("fragonib", "fragonib[AT]yahoo[DOT]es"),
                       ("the-razer", "daniel_ AT gmx DOT net"),
                       ("zoidberg", "zoidberg@mujmail.cz"),
                       ("imclem", None),
                       ("stickell", "l.stickell@yahoo.it"),
                       ("Elrick69", "elrick69[AT]rocketmail[DOT]com"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    NAME_PATTERN = r'>FileName :</td>\s*<td.*>(?P<N>.+?)<'
    SIZE_PATTERN = r'>Size :</td>\s*<td.*>(?P<S>[\d.,]+) (?P<U>[\w^_]+)'

    OFFLINE_PATTERN = r'File not found !\s*<'

    COOKIES = [("1fichier.com", "LG", "en")]

    WAIT_PATTERN = r'>You must wait (\d+)'


    def setup(self):
        self.multiDL = self.premium
        self.resumeDownload = True


    def handle(self, reconnect):
        m = re.search(self.WAIT_PATTERN, self.html)
        if m:
            wait_time = int(m.group(1)) * 60

            self.wait(wait_time, reconnect)
            self.retry(reason="You have to wait been each free download")

        id = self.info['ID1'] or self.info['ID2']
        url, inputs = self.parseHtmlForm('action="https://1fichier.com/\?%s' % id)

        if not url:
            self.fail(_("Download link not found"))

        if "pass" in inputs:
            inputs['pass'] = self.getPassword()

        inputs['submit'] = "Download"

        self.download(url, post=inputs)


    def handleFree(self):
        return self.handle(True)


    def handlePremium(self):
        return self.handle(False)


getInfo = create_getInfo(OneFichierCom)
