# -*- coding: utf-8 -*-

import re

from time import time

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class MegasharesCom(SimpleHoster):
    __name__    = "MegasharesCom"
    __type__    = "hoster"
    __version__ = "0.28"

    __pattern__ = r'http://(?:www\.)?(d\d{2}\.)?megashares\.com/((index\.php)?\?d\d{2}=|dl/)\w+'

    __description__ = """Megashares.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    NAME_PATTERN = r'<h1 class="black xxl"[^>]*title="(?P<N>[^"]+)">'
    SIZE_PATTERN = r'<strong><span class="black">Filesize:</span></strong> (?P<S>[\d.,]+) (?P<U>[\w^_]+)'
    OFFLINE_PATTERN = r'<dd class="red">(Invalid Link Request|Link has been deleted|Invalid link)'

    LINK_PATTERN = r'<div id="show_download_button_%d"[^>]*>\s*<a href="([^"]+)">'

    PASSPORT_LEFT_PATTERN = r'Your Download Passport is: <[^>]*>(\w+).*?You have.*?<[^>]*>.*?([\d.]+) (\w+)'
    PASSPORT_RENEW_PATTERN = r'(\d+):<strong>(\d+)</strong>:<strong>(\d+)</strong>'
    REACTIVATE_NUM_PATTERN = r'<input[^>]*id="random_num" value="(\d+)" />'
    REACTIVATE_PASSPORT_PATTERN = r'<input[^>]*id="passport_num" value="(\w+)" />'
    REQUEST_URI_PATTERN = r'var request_uri = "([^"]+)";'
    NO_SLOTS_PATTERN = r'<dd class="red">All download slots for this link are currently filled'


    def setup(self):
        self.resumeDownload = True
        self.multiDL        = self.premium


    def handlePremium(self, pyfile):
        self.handleDownload(True)


    def handleFree(self, pyfile):
        if self.NO_SLOTS_PATTERN in self.html:
            self.retry(wait_time=5 * 60)

        m = re.search(self.REACTIVATE_PASSPORT_PATTERN, self.html)
        if m:
            passport_num = m.group(1)
            request_uri = re.search(self.REQUEST_URI_PATTERN, self.html).group(1)

            for _i in xrange(5):
                random_num = re.search(self.REACTIVATE_NUM_PATTERN, self.html).group(1)

                verifyinput = self.decryptCaptcha("http://d01.megashares.com/index.php",
                                                  get={'secgfx': "gfx", 'random_num': random_num})

                self.logInfo(_("Reactivating passport %s: %s %s") % (passport_num, random_num, verifyinput))

                res = self.load("http://d01.megashares.com%s" % request_uri,
                                get={'rs'      : "check_passport_renewal",
                                     'rsargs[]': verifyinput,
                                     'rsargs[]': random_num,
                                     'rsargs[]': passport_num,
                                     'rsargs[]': "replace_sec_pprenewal",
                                     'rsrnd[]' : str(int(time() * 1000))})

                if 'Thank you for reactivating your passport.' in res:
                    self.correctCaptcha()
                    self.retry()
                else:
                    self.invalidCaptcha()
            else:
                self.fail(_("Failed to reactivate passport"))

        m = re.search(self.PASSPORT_RENEW_PATTERN, self.html)
        if m:
            time = [int(x) for x in m.groups()]
            renew = time[0] + (time[1] * 60) + (time[2] * 60)
            self.logDebug("Waiting %d seconds for a new passport" % renew)
            self.retry(wait_time=renew, reason=_("Passport renewal"))

        # Check traffic left on passport
        m = re.search(self.PASSPORT_LEFT_PATTERN, self.html, re.M | re.S)
        if m is None:
            self.fail(_("Passport not found"))

        self.logInfo(_("Download passport: %s") % m.group(1))
        data_left = float(m.group(2)) * 1024 ** {'B': 0, 'KB': 1, 'MB': 2, 'GB': 3}[m.group(3)]
        self.logInfo(_("Data left: %s %s (%d MB needed)") % (m.group(2), m.group(3), self.pyfile.size / 1048576))

        if not data_left:
            self.retry(wait_time=600, reason=_("Passport renewal"))

        self.handleDownload(False)


    def handleDownload(self, premium=False):
        # Find download link;
        m = re.search(self.LINK_PATTERN % (1 if premium else 2), self.html)
        msg = _('%s download URL' % ('Premium' if premium else 'Free'))
        if m is None:
            self.error(msg)

        download_url = m.group(1)
        self.logDebug("%s: %s" % (msg, download_url))
        self.download(download_url)


getInfo = create_getInfo(MegasharesCom)
