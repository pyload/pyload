# -*- coding: utf-8 -*
#
# Test links:
#   https://s.basketbuild.com/filedl/devs?dev=pacman&dl=pacman/falcon/RC-3/pac_falcon-RC-3-20141103.zip
#   https://s.basketbuild.com/filedl/gapps?dl=gapps-gb-20110828-signed.zip

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class BasketbuildCom(SimpleHoster):
    __name__    = "BasketbuildCom"
    __type__    = "hoster"
    __version__ = "0.04"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?(?:\w\.)?basketbuild\.com/filedl/.+'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """Basketbuild.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zapp-brannigan", "fuerst.reinje@web.de")]


    NAME_PATTERN    = r'File Name:</strong> (?P<N>.+?)<br/>'
    SIZE_PATTERN    = r'File Size:</strong> (?P<S>[\d.,]+) (?P<U>[\w^_]+)'
    OFFLINE_PATTERN = r'404 - Page Not Found'


    def setup(self):
        self.multiDL        = True
        self.resume_download = True
        self.chunk_limit     = 1


    def handle_free(self, pyfile):
        try:
            link1 = re.search(r'href="(.+dlgate/.+)"', self.html).group(1)
            self.html = self.load(link1)

        except AttributeError:
            self.error(_("Hop #1 not found"))

        else:
            self.log_debug("Next hop: %s" % link1)

        try:
            wait = re.search(r'var sec = (\d+)', self.html).group(1)
            self.log_debug("Wait %s seconds" % wait)
            self.wait(wait)

        except AttributeError:
            self.log_debug("No wait time found")

        try:
            self.link = re.search(r'id="dlLink">\s*<a href="(.+?)"', self.html).group(1)

        except AttributeError:
            self.error(_("DL-Link not found"))


getInfo = create_getInfo(BasketbuildCom)
