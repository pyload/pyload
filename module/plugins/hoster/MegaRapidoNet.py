# -*- coding: utf-8 -*-

import random

from module.plugins.internal.MultiHoster import MultiHoster


def random_with_n_digits(n):
    rand = "0."
    not_zero = 0
    for i in xrange(1, n + 1):
        r = random.randint(0, 9)
        if(r > 0):
            not_zero += 1
        rand += str(r)

    if not_zero > 0:
        return rand
    else:
        return random_with_N_digits(n)


class MegaRapidoNet(MultiHoster):
    __name__    = "MegaRapidoNet"
    __type__    = "hoster"
    __version__ = "0.04"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?\w+\.megarapido\.net/\?file=\w+'
    __config__  = [("use_premium" , "bool", "Use premium account if available"    , True),
                   ("revertfailed", "bool", "Revert to standard download if fails", True)]

    __description__ = """MegaRapido.net multi-hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Kagenoshin", "kagenoshin@gmx.ch")]


    LINK_PREMIUM_PATTERN = r'<\s*?a[^>]*?title\s*?=\s*?["\'].*?download["\'][^>]*?href=["\']([^"\']+)'

    ERROR_PATTERN = r'<\s*?div[^>]*?class\s*?=\s*?["\']?alert-message error.*?>([^<]*)'


    def handle_premium(self, pyfile):
        self.html = self.load("http://megarapido.net/gerar.php",
                         post={'rand'     :random_with_N_digits(16),
                               'urllist'  : pyfile.url,
                               'links'    : pyfile.url,
                               'exibir'   : "normal",
                               'usar'     : "premium",
                               'user'     : self.account.get_data(self.user).get('sid', None),
                               'autoreset': ""})

        if "desloga e loga novamente para gerar seus links" in self.html.lower():
            self.error("You have logged in at another place")

        return super(MegaRapidoNet, self).handle_premium(pyfile)
