# -*- coding: utf-8 -*-

import re

from time import time

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class MegasharesCom(SimpleHoster):
    __name__ = "MegasharesCom"
    __type__ = "hoster"
    __version__ = "0.24"

    __pattern__ = r'http://(?:www\.)?megashares.com/.*'

    __description__ = """Megashares.com hoster plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"

    FILE_NAME_PATTERN = r'<h1 class="black xxl"[^>]*title="(?P<N>[^"]+)">'
    FILE_SIZE_PATTERN = r'<strong><span class="black">Filesize:</span></strong> (?P<S>[0-9.]+) (?P<U>[kKMG])i?B<br />'
    OFFLINE_PATTERN = r'<dd class="red">(Invalid Link Request|Link has been deleted)'

    LINK_PATTERN = r'<div id="show_download_button_%d"[^>]*>\s*<a href="([^"]+)">'
    PASSPORT_LEFT_PATTERN = r'Your Download Passport is: <[^>]*>(\w+).*\s*You have\s*<[^>]*>\s*([0-9.]+) ([kKMG]i?B)'
    PASSPORT_RENEW_PATTERN = r'Your download passport will renew in\s*<strong>(\d+)</strong>:<strong>(\d+)</strong>:<strong>(\d+)</strong>'
    REACTIVATE_NUM_PATTERN = r'<input[^>]*id="random_num" value="(\d+)" />'
    REACTIVATE_PASSPORT_PATTERN = r'<input[^>]*id="passport_num" value="(\w+)" />'
    REQUEST_URI_PATTERN = r'var request_uri = "([^"]+)";'
    NO_SLOTS_PATTERN = r'<dd class="red">All download slots for this link are currently filled'


    def setup(self):
        self.resumeDownload = True
        self.multiDL = self.premium

    def handlePremium(self):
        self.handleDownload(True)

    def handleFree(self):
        self.html = self.load(self.pyfile.url, decode=True)

        if self.NO_SLOTS_PATTERN in self.html:
            self.retry(wait_time=5 * 60)

        self.getFileInfo()
        # if self.pyfile.size > 576716800:
        #     self.fail("This file is too large for free download")

        # Reactivate passport if needed
        m = re.search(self.REACTIVATE_PASSPORT_PATTERN, self.html)
        if m:
            passport_num = m.group(1)
            request_uri = re.search(self.REQUEST_URI_PATTERN, self.html).group(1)

            for _ in xrange(5):
                random_num = re.search(self.REACTIVATE_NUM_PATTERN, self.html).group(1)

                verifyinput = self.decryptCaptcha(
                    "http://d01.megashares.com/index.php?secgfx=gfx&random_num=%s" % random_num)
                self.logInfo("Reactivating passport %s: %s %s" % (passport_num, random_num, verifyinput))

                url = ("http://d01.megashares.com%s&rs=check_passport_renewal" % request_uri +
                       "&rsargs[]=%s&rsargs[]=%s&rsargs[]=%s" % (verifyinput, random_num, passport_num) +
                       "&rsargs[]=replace_sec_pprenewal&rsrnd=%s" % str(int(time() * 1000)))
                self.logDebug(url)
                response = self.load(url)

                if 'Thank you for reactivating your passport.' in response:
                    self.correctCaptcha()
                    self.retry()
                else:
                    self.invalidCaptcha()
            else:
                self.fail("Failed to reactivate passport")

        # Check traffic left on passport
        m = re.search(self.PASSPORT_LEFT_PATTERN, self.html)
        if m is None:
            self.fail('Passport not found')
        self.logInfo("Download passport: %s" % m.group(1))
        data_left = float(m.group(2)) * 1024 ** {'KB': 1, 'MB': 2, 'GB': 3}[m.group(3)]
        self.logInfo("Data left: %s %s (%d MB needed)" % (m.group(2), m.group(3), self.pyfile.size / 1048576))

        if not data_left:
            m = re.search(self.PASSPORT_RENEW_PATTERN, self.html)
            renew = m.group(1) + m.group(2) + m.group(3) * 60 * 60 if m else 10 * 60
            self.retry(max_tries=15, wait_time=renew, reason="Unable to get passport")

        self.handleDownload(False)

    def handleDownload(self, premium=False):
        # Find download link;
        m = re.search(self.LINK_PATTERN % (1 if premium else 2), self.html)
        msg = '%s download URL' % ('Premium' if premium else 'Free')
        if m is None:
            self.parseError(msg)

        download_url = m.group(1)
        self.logDebug("%s: %s" % (msg, download_url))
        self.download(download_url)


getInfo = create_getInfo(MegasharesCom)
