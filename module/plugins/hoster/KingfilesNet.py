# -*- coding: utf-8 -*-

import re

from module.plugins.captcha.SolveMedia import SolveMedia
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class KingfilesNet(SimpleHoster):
    __name__    = "KingfilesNet"
    __type__    = "hoster"
    __version__ = "0.09"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?kingfiles\.net/(?P<ID>\w{12})'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """Kingfiles.net hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zapp-brannigan", "fuerst.reinje@web.de"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    NAME_PATTERN = r'name="fname" value="(?P<N>.+?)">'
    SIZE_PATTERN = r'>Size: .+?">(?P<S>[\d.,]+) (?P<U>[\w^_]+)'

    OFFLINE_PATTERN = r'>(File Not Found</b><br><br>|File Not Found</h2>)'

    RAND_ID_PATTERN = r'type=\"hidden\" name=\"rand\" value=\"(.+)\">'

    LINK_FREE_PATTERN = r'var download_url = \'(.+)\';'


    def setup(self):
        self.resume_download = True
        self.multiDL        = True


    def handle_free(self, pyfile):
        #: Click the free user button
        post_data = {'op'         : "download1",
                     'usr_login'  : "",
                     'id'         : self.info['pattern']['ID'],
                     'fname'      : pyfile.name,
                     'referer'    : "",
                     'method_free': "+"}

        self.html = self.load(pyfile.url, post=post_data)

        solvemedia = SolveMedia(self)
        response, challenge = solvemedia.challenge()

        #: Make the downloadlink appear and load the file
        m = re.search(self.RAND_ID_PATTERN, self.html)
        if m is None:
            self.error(_("Random key not found"))

        rand = m.group(1)
        self.log_debug("rand = ", rand)

        post_data = {'op'              : "download2",
                     'id'              : self.info['pattern']['ID'],
                     'rand'            : rand,
                     'referer'         : pyfile.url,
                     'method_free'     : "+",
                     'method_premium'  : "",
                     'adcopy_response' : response,
                     'adcopy_challenge': challenge,
                     'down_direct'     : "1"}

        self.html = self.load(pyfile.url, post=post_data)

        m = re.search(self.LINK_FREE_PATTERN, self.html)
        if m is None:
            self.error(_("Download url not found"))

        self.link = m.group(1)


getInfo = create_getInfo(KingfilesNet)
