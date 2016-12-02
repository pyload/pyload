# -*- coding: utf-8 -*-

# Test links (random.bin):
# http://5pnm24ltcw.1fichier.com/

import re
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class OneFichierCom(SimpleHoster):
    __name__ = "OneFichierCom"
    __type__ = "hoster"
    __pattern__ = r'(http://(\w+)\.((1fichier|d(es)?fichiers|pjointe)\.(com|fr|net|org)|(cjoint|mesfichiers|piecejointe|oi)\.(org|net)|tenvoi\.(com|org|net)|dl4free\.com|alterupload\.com|megadl.fr))'
    __version__ = "0.50"
    __description__ = """1fichier.com hoster plugin"""
    __author_name__ = ("fragonib", "the-razer", "zoidberg", "imclem")
    __author_mail__ = ("fragonib[AT]yahoo[DOT]es", "daniel_ AT gmx DOT net", "zoidberg@mujmail.cz", "imclem on github")

    FILE_NAME_PATTERN = r'">Filename :</th>\s*<td>(?P<N>[^<]+)</td>'
    FILE_SIZE_PATTERN = r'<th>Size :</th>\s*<td>(?P<S>[^<]+)</td>'
    FILE_OFFLINE_PATTERN = r'The (requested)? file (could not be found|has been deleted)'
    FILE_URL_REPLACEMENTS = [(r'(http://[^/]*).*', r'\1/en/')]

    DOWNLOAD_LINK_PATTERN = r"""location\s*.\s*'(?P<N>http://.*?)'"""
    PASSWORD_PROTECTED_TOKEN = "protected by password"
    WAITING_PATTERN = "Warning ! Without premium status, you must wait up to (\d+) minutes between each downloads"
    LAST_DOWNLOAD_DELAY = "Your last download finished (\d+) minutes ago"
    NOT_PARALLEL = r"Warning ! Without premium status, you can download only one file at a time"
    RETRY_TIME = 15*60  # Default retry time in seconds (if detected parallel download)

    def process(self, pyfile):
        found = re.match(self.__pattern__, pyfile.url)
        file_id = found.group(2)
        url = "http://%s.%s/en/" % (found.group(2), found.group(3))
        self.html = self.load(url, decode=True)

        self.getFileInfo()

        found = re.search(self.WAITING_PATTERN, self.html)
        if found:
            last_delay = 0
            # retrieve the delay from the last download to substract from required delay
            found_delay = re.search(self.LAST_DOWNLOAD_DELAY, self.html)
            if found_delay:
                last_delay = int(found_delay.group(1))
            self.waitAndRetry((int(found.group(1)) - last_delay) * 60)
        else:  # detect parallel download
            found = re.search(self.NOT_PARALLEL, self.html)
            if found:
                self.waitAndRetry(self.RETRY_TIME)

        url, inputs = self.parseHtmlForm('action="http://%s' % file_id)
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

    def setup(self):
        self.multiDL = self.premium
        self.resumeDownload = True

getInfo = create_getInfo(OneFichierCom)
