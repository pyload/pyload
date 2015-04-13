# -*- coding: utf-8 -*
#
# Test links:
#   https://s.basketbuild.com/filedl/devs?dev=pacman&dl=pacman/falcon/RC-3/pac_falcon-RC-3-20141103.zip
#   https://s.basketbuild.com/filedl/gapps?dl=gapps-gb-20110828-signed.zip

import re

from pyload.plugin.internal.SimpleHoster import SimpleHoster


class BasketbuildCom(SimpleHoster):
    __name    = "BasketbuildCom"
    __type    = "hoster"
    __version = "0.03"

    __pattern = r'https?://(?:www\.)?(?:\w\.)?basketbuild\.com/filedl/.+'
    __config  = [("use_premium", "bool", "Use premium account if available", True)]

    __description = """basketbuild.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zapp-brannigan", "fuerst.reinje@web.de")]


    NAME_PATTERN    = r'File Name:</strong> (?P<N>.+?)<br/>'
    SIZE_PATTERN    = r'File Size:</strong> (?P<S>[\d.,]+) (?P<U>[\w^_]+)'
    OFFLINE_PATTERN = r'404 - Page Not Found'


    def setup(self):
        self.multiDL        = True
        self.resumeDownload = True
        self.chunkLimit     = 1


    def handleFree(self, pyfile):
        try:
            link1 = re.search(r'href="(.+dlgate/.+)"', self.html).group(1)
            self.html = self.load(link1)

        except AttributeError:
            self.error(_("Hop #1 not found"))

        else:
            self.logDebug("Next hop: %s" % link1)

        try:
            wait = re.search(r'var sec = (\d+)', self.html).group(1)
            self.logDebug("Wait %s seconds" % wait)
            self.wait(wait)

        except AttributeError:
            self.logDebug("No wait time found")

        try:
            self.link = re.search(r'id="dlLink">\s*<a href="(.+?)"', self.html).group(1)

        except AttributeError:
            self.error(_("DL-Link not found"))
