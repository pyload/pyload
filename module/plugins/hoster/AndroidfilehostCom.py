# -*- coding: utf-8 -*
#
# Test links:
#   https://www.androidfilehost.com/?fid=95916177934518197

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class AndroidfilehostCom(SimpleHoster):
    __name__    = "AndroidfilehostCom"
    __type__    = "hoster"
    __version__ = "0.01"

    __pattern__ = r'https?://(?:www\.)?androidfilehost\.com/\?fid=\d+'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """Androidfilehost.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zapp-brannigan", "fuerst.reinje@web.de")]


    NAME_PATTERN    = r'<br />(?P<N>.*?)</h1>'
    SIZE_PATTERN    = r'<h4>size</h4>\s*<p>(?P<S>[\d.,]+)(?P<U>[\w^_]+)</p>'
    HASHSUM_PATTERN = r'<h4>(?P<T>.*?)</h4>\s*<p><code>(?P<H>.*?)</code></p>'

    OFFLINE_PATTERN = r'404 not found'

    WAIT_PATTERN    = r'users must wait <strong>(\d+) secs'


    def setup(self):
        self.multiDL        = True
        self.resumeDownload = True
        self.chunkLimit     = 1


    def handleFree(self, pyfile):
        wait = re.search(self.WAIT_PATTERN, self.html)
        self.logDebug("Waiting time: %s seconds" % wait.group(1))

        fid = re.search(r'id="fid" value="(\d+)" />', self.html).group(1)
        self.logDebug("fid: %s" % fid)

        html = self.load("https://www.androidfilehost.com/libs/otf/mirrors.otf.php",
                         post={'submit': 'submit',
                               'action': 'getdownloadmirrors',
                               'fid'   : fid},
                         decode=True)

        self.link   = re.findall('"url":"(.*?)"', html)[0].replace("\\", "")
        mirror_host = self.link.split("/")[2]

        self.logDebug("Mirror Host: %s" % mirror_host)

        html = self.load("https://www.androidfilehost.com/libs/otf/stats.otf.php",
                         get={'fid'   : fid,
                              'w'     : 'download',
                              'mirror': mirror_host},
                         decode=True)


getInfo = create_getInfo(AndroidfilehostCom)
