# -*- coding: utf-8 -*-

import re

from pyload.network.RequestFactory import getURL
from pyload.plugins.base.Hook import Hook
from pyload.utils import remove_chars


class LinkdecrypterCom(Hook):
    __name__    = "LinkdecrypterCom"
    __type__    = "hook"
    __version__ = "0.20"

    __description__ = """Linkdecrypter.com hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    def coreReady(self):
        try:
            self.loadPatterns()
        except Exception, e:
            self.logError(e)


    def loadPatterns(self):
        html = getURL("http://linkdecrypter.com/")

        m = re.search(r'<title>', html)
        if m is None:
            self.logError(_("Linkdecrypter site is down"))
            return

        m = re.search(r'<b>Supported\(\d+\)</b>: <i>([^+<]*)', html)
        if m is None:
            self.logError(_("Crypter list not found"))
            return

        builtin = [name.lower() for name in self.core.pluginManager.crypterPlugins.keys()]
        builtin.append("downloadserienjunkiesorg")

        crypter_pattern = re.compile("(\w[\w.-]+)")
        online = []
        for crypter in m.group(1).split(', '):
            m = re.match(crypter_pattern, crypter)
            if m and remove_chars(m.group(1), "-.") not in builtin:
                online.append(m.group(1).replace(".", "\\."))

        if not online:
            self.logError(_("Crypter list is empty"))
            return

        regexp = r'https?://([^.]+\.)*?(%s)/.*' % '|'.join(online)

        dict = self.core.pluginManager.crypterPlugins[self.__name__]
        dict['pattern'] = regexp
        dict['re'] = re.compile(regexp)

        self.logDebug("Loaded pattern: %s" % regexp)
