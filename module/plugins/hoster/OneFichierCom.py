# -*- coding: utf-8 -*-

# Test links (random.bin):
# http://5pnm24ltcw.1fichier.com/

import re
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class OneFichierCom(SimpleHoster):
    __name__ = "OneFichierCom"
    __type__ = "hoster"
    __pattern__ = r"(http://(\w+)\.((1fichier|d(es)?fichiers|pjointe)\.(com|fr|net|org)|(cjoint|mesfichiers|piecejointe|oi)\.(org|net)|tenvoi\.(com|org|net)|dl4free\.com|alterupload\.com|megadl.fr))"
    __version__ = "0.49"
    __description__ = """1fichier.com download hoster"""
    __author_name__ = ("fragonib", "the-razer", "zoidberg", "imclem")
    __author_mail__ = ("fragonib[AT]yahoo[DOT]es", "daniel_ AT gmx DOT net", "zoidberg@mujmail.cz", "imclem on github")

    FILE_NAME_PATTERN = r'">Filename :</th>\s*<td>(?P<N>[^<]+)</td>'
    FILE_SIZE_PATTERN = r'<th>Size :</th>\s*<td>(?P<S>[^<]+)</td>'
    FILE_OFFLINE_PATTERN = r'The (requested)? file (could not be found|has been deleted)'
    FILE_URL_REPLACEMENTS = [(r'(http://[^/]*).*', r'\1/en/')]

    DOWNLOAD_LINK_PATTERN = r"""location\s*.\s*'(?P<N>http://.*?)'"""
    PASSWORD_PROTECTED_TOKEN = "protected by password"
    WAITING_PATTERN = "Warning ! Without premium status, you can download only one file at a time and you must wait up to (\d+) minutes between each downloads."

    def process(self, pyfile):
        found = re.search(self.__pattern__, pyfile.url)
        file_id = found.group(2)
        url = "http://%s.%s/en/" % (found.group(2), found.group(3))
        self.html = self.load(url, post="submit", decode=True)

        found = re.search(self.WAITING_PATTERN, self.html)
        if found:
            self.waitAndRetry(int(found.group(1)) * 60)

        self.getFileInfo()

        url, inputs = self.parseHtmlForm('action="http://%s' % file_id)
        if not url or not inputs:
            self.parseError("Download link not found")

        # Check for protection 
        if "pass" in inputs:
            inputs['pass'] = self.getPassword()

        self.html = self.load(url, post=inputs)
        m = re.search(self.DOWNLOAD_LINK_PATTERN, self.html)
        if not m:
            self.parseError("Unable to detect download link")
        download_url = m.group(1)

        self.download(download_url)

        # Check download 
        self.checkDownloadedFile()

    def checkDownloadedFile(self):
        check = self.checkDownload({"wait": self.WAITING_PATTERN})
        if check == "wait":
            self.waitAndRetry(int(self.lastcheck.group(1)) * 60)

    def waitAndRetry(self, wait_time):
        self.setWait(wait_time, True)
        self.wait()
        self.retry()

    def setup(self):
        self.multiDL = self.premium
        self.resumeDownload = True

getInfo = create_getInfo(OneFichierCom)   
