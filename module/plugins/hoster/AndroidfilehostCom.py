# -*- coding: utf-8 -*

import pycurl
import re

from ..internal.SimpleHoster import SimpleHoster


class AndroidfilehostCom(SimpleHoster):
    __name__ = "AndroidfilehostCom"
    __type__ = "hoster"
    __version__ = "0.07"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.)?androidfilehost\.com/\?fid=\d+'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool", "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Androidfilehost.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zapp-brannigan", "fuerst.reinje@web.de")]

    NAME_PATTERN = r'name="filename" id="filename" value="(?P<N>.*?)" />'
    SIZE_PATTERN = r'<span class="file-attr-value">(?P<S>[\d.,]+)(?P<U>[\w^_]+)<br><span class="file-attr-label">Size</span></span>'
    HASHSUM_PATTERN = r'<span class="file-attr-value">(?P<D>.*?)<br><span class="file-attr-label">(?P<H>MD5)</span></span>'

    OFFLINE_PATTERN = r'404 not found'
    TEMP_OFFLINE_PATTERN = r'[^\w](503\s|[Mm]aint(e|ai)nance|[Tt]emp([.-]|orarily))'

    WAIT_PATTERN = r'users must wait <strong>(\d+) secs'

    def setup(self):
        self.multiDL = True
        self.resume_download = True
        self.chunk_limit = 1

    def handle_free(self, pyfile):
        wait = re.search(self.WAIT_PATTERN, self.data)
        if wait is not None :
            self.log_debug("Waiting time: %s seconds" % wait.group(1))

        fid = re.search(r'id="fid" value="(\d+)" />', self.data).group(1)
        self.log_debug("FID: %s" % fid)

        self.req.http.c.setopt(pycurl.HTTPHEADER, ["X-MOD-SBB-CTYPE: xhr"])

        html = self.load("https://androidfilehost.com/libs/otf/mirrors.otf.php",
                         post={'submit': 'submit',
                               'action': 'getdownloadmirrors',
                               'fid': fid})
        self.req.http.c.setopt(pycurl.HTTPHEADER, ["X-MOD-SBB-CTYPE:"])


        self.link = re.findall('"url":"(.*?)"', html)[0].replace("\\", "")
        mirror_host = self.link.split("/")[2]

        self.log_debug("Mirror Host: %s" % mirror_host)

        html = self.load("https://androidfilehost.com/libs/otf/stats.otf.php",
                         get={'fid': fid,
                              'w': 'download',
                              'mirror': mirror_host})
