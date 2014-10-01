# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class OneFichierCom(SimpleHoster):
    __name__ = "OneFichierCom"
    __type__ = "hoster"
    __version__ = "0.62"

    __pattern__ = r'https?://(?P<ID>\w+)\.(?P<HOST>(1fichier|d(es)?fichiers|pjointe)\.(com|fr|net|org)|(cjoint|mesfichiers|piecejointe|oi)\.(org|net)|tenvoi\.(com|org|net)|dl4free\.com|alterupload\.com|megadl\.fr)'

    __description__ = """1fichier.com hoster plugin"""
    __author_name__ = ("fragonib", "the-razer", "zoidberg", "imclem", "stickell", "Elrick69")
    __author_mail__ = ("fragonib[AT]yahoo[DOT]es", "daniel_ AT gmx DOT net", "zoidberg@mujmail.cz",
                       "imclem on github", "l.stickell@yahoo.it", "elrick69[AT]rocketmail[DOT]com")


    FILE_NAME_PATTERN = r'>Filename :</th>\s*<td>(?P<N>.+?)<'
    FILE_SIZE_PATTERN = r'>Size :</th>\s*<td>(?P<S>[\d.,]+) (?P<U>\w+)'
    OFFLINE_PATTERN = r'>The (requested)? file (could not be found|has been deleted)'

    FILE_URL_REPLACEMENTS = [(__pattern__, r'http://\g<ID>.\g<HOST>/en/')]

    WAIT_PATTERN = r'>You must wait (\d+)'


    def setup(self):
        self.multiDL = True
        self.resumeDownload = True


    def handleFree(self):
        self.html = self.load(self.pyfile.url, decode=True)
        m = re.search(self.WAIT_PATTERN, self.html)
        if m:
            time = int(m.group(1)) + 1 * 60  #: One minute more than what the page displays to be safe
            self.logInfo("You have to wait been each free download", "Retrying in %d minutes." % minutes)
            self.wait(time, True)
            self.retry()

        url, inputs = self.parseHtmlForm('action="http://%s' % self.file_info['ID'])
        if not url:
            self.parseError("Download link not found")

        # Check for protection
        if "pass" in inputs:
            inputs['pass'] = self.getPassword()
        inputs['submit'] = "Download"

        self.download(url, post=inputs)

        # Check download
        self.checkDownloadedFile()


    def handlePremium(self):
        url, inputs = self.parseHtmlForm('action="http://%s' % self.file_info['ID'])
        if not url:
            self.parseError("Download link not found")

        # Check for protection
        if "pass" in inputs:
            inputs['pass'] = self.getPassword()
        inputs['submit'] = "Download"

        self.download(url, post=inputs)

        # Check download
        self.checkDownloadedFile()


    def checkDownloadedFile(self):
        check = self.checkDownload({'wait': self.WAIT_PATTERN})
        if check == "wait":
            time = int(self.lastcheck.group(1)) * 60
            self.wait(time, True)
            self.retry()


getInfo = create_getInfo(OneFichierCom)
