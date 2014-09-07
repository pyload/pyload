# -*- coding: utf-8 -*-
#
# Test links:
# http://5pnm24ltcw.1fichier.com/

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class OneFichierCom(SimpleHoster):
    __name__ = "OneFichierCom"
    __type__ = "hoster"
    __version__ = "0.61"

    __pattern__ = r'(http://(?P<id>\w+)\.(?P<host>(1fichier|d(es)?fichiers|pjointe)\.(com|fr|net|org)|(cjoint|mesfichiers|piecejointe|oi)\.(org|net)|tenvoi\.(com|org|net)|dl4free\.com|alterupload\.com|megadl.fr))/?'

    __description__ = """1fichier.com hoster plugin"""
    __author_name__ = ("fragonib", "the-razer", "zoidberg", "imclem", "stickell", "Elrick69")
    __author_mail__ = ("fragonib[AT]yahoo[DOT]es", "daniel_ AT gmx DOT net", "zoidberg@mujmail.cz",
                       "imclem on github", "l.stickell@yahoo.it", "elrick69[AT]rocketmail[DOT]com")

    FILE_NAME_PATTERN = r'">Filename :</th>\s*<td>(?P<N>[^<]+)</td>'
    FILE_SIZE_PATTERN = r'<th>Size :</th>\s*<td>(?P<S>[^<]+)</td>'
    OFFLINE_PATTERN = r'The (requested)? file (could not be found|has been deleted)'

    FILE_URL_REPLACEMENTS = [(__pattern__, r'http://\g<id>.\g<host>/en/')]

    WAITING_PATTERN = r'Warning ! Without premium status, you must wait between each downloads'
    NOT_PARALLEL = r'Warning ! Without premium status, you can download only one file at a time'
    WAIT_TIME = 10 * 60  # Retry time between each free download
    RETRY_TIME = 15 * 60  # Default retry time in seconds (if detected parallel download)


    def setup(self):
        self.multiDL = self.premium
        self.resumeDownload = True

    def handleFree(self):
        self.html = self.load(self.pyfile.url, decode=True)

        if self.WAITING_PATTERN in self.html:
            self.logInfo('You have to wait been each free download! Retrying in %d seconds.' % self.WAIT_TIME)
            self.waitAndRetry(self.WAIT_TIME)
        else:  # detect parallel download
            m = re.search(self.NOT_PARALLEL, self.html)
            if m:
                self.waitAndRetry(self.RETRY_TIME)

        url, inputs = self.parseHtmlForm('action="http://%s' % self.file_info['id'])
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
        url, inputs = self.parseHtmlForm('action="http://%s' % self.file_info['id'])
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
        check = self.checkDownload({"wait": self.WAITING_PATTERN})
        if check == "wait":
            self.waitAndRetry(int(self.lastcheck.group(1)) * 60)

    def waitAndRetry(self, wait_time):
        self.wait(wait_time, True)
        self.retry()



getInfo = create_getInfo(OneFichierCom)
