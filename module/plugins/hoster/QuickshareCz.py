# -*- coding: utf-8 -*-

import re

from pycurl import FOLLOWLOCATION

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class QuickshareCz(SimpleHoster):
    __name__ = "QuickshareCz"
    __type__ = "hoster"
    __version__ = "0.54"

    __pattern__ = r'http://(?:[^/]*\.)?quickshare.cz/stahnout-soubor/.*'

    __description__ = """Quickshare.cz hoster plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"

    FILE_NAME_PATTERN = r'<th width="145px">Název:</th>\s*<td style="word-wrap:break-word;">(?P<N>[^<]+)</td>'
    FILE_SIZE_PATTERN = r'<th>Velikost:</th>\s*<td>(?P<S>[0-9.]+) (?P<U>[kKMG])i?B</td>'
    OFFLINE_PATTERN = r'<script type="text/javascript">location.href=\'/chyba\';</script>'


    def process(self, pyfile):
        self.html = self.load(pyfile.url, decode=True)
        self.getFileInfo()

        # parse js variables
        self.jsvars = dict((x, y.strip("'")) for x, y in re.findall(r"var (\w+) = ([0-9.]+|'[^']*')", self.html))
        self.logDebug(self.jsvars)
        pyfile.name = self.jsvars['ID3']

        # determine download type - free or premium
        if self.premium:
            if 'UU_prihlasen' in self.jsvars:
                if self.jsvars['UU_prihlasen'] == '0':
                    self.logWarning('User not logged in')
                    self.relogin(self.user)
                    self.retry()
                elif float(self.jsvars['UU_kredit']) < float(self.jsvars['kredit_odecet']):
                    self.logWarning('Not enough credit left')
                    self.premium = False

        if self.premium:
            self.handlePremium()
        else:
            self.handleFree()

        check = self.checkDownload({"err": re.compile(r"\AChyba!")}, max_size=100)
        if check == "err":
            self.fail("File not m or plugin defect")

    def handleFree(self):
        # get download url
        download_url = '%s/download.php' % self.jsvars['server']
        data = dict((x, self.jsvars[x]) for x in self.jsvars if x in ("ID1", "ID2", "ID3", "ID4"))
        self.logDebug("FREE URL1:" + download_url, data)

        self.req.http.c.setopt(FOLLOWLOCATION, 0)
        self.load(download_url, post=data)
        self.header = self.req.http.header
        self.req.http.c.setopt(FOLLOWLOCATION, 1)

        m = re.search("Location\s*:\s*(.*)", self.header, re.I)
        if m is None:
            self.fail('File not found')
        download_url = m.group(1)
        self.logDebug("FREE URL2:" + download_url)

        # check errors
        m = re.search(r'/chyba/(\d+)', download_url)
        if m:
            if m.group(1) == '1':
                self.retry(60, 2 * 60, "This IP is already downloading")
            elif m.group(1) == '2':
                self.retry(60, 60, "No free slots available")
            else:
                self.fail('Error %d' % m.group(1))

        # download file
        self.download(download_url)

    def handlePremium(self):
        download_url = '%s/download_premium.php' % self.jsvars['server']
        data = dict((x, self.jsvars[x]) for x in self.jsvars if x in ("ID1", "ID2", "ID4", "ID5"))
        self.logDebug("PREMIUM URL:" + download_url, data)
        self.download(download_url, get=data)


getInfo = create_getInfo(QuickshareCz)
