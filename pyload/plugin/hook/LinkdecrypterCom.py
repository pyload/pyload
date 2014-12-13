# -*- coding: utf-8 -*-

import re

from pyload.network.RequestFactory import getURL
from pyload.plugin.Addon import Addon
from pyload.utils import remove_chars


class LinkdecrypterCom(Addon):
    __name    = "LinkdecrypterCom"
    __type    = "hook"
    __version = "0.21"

    __description = """Linkdecrypter.com hook plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]


    def activate(self):
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

        dict = self.core.pluginManager.crypterPlugins[self.__name]
        dict['pattern'] = regexp
        dict['re'] = re.compile(regexp)

        self.logDebug("Loaded pattern: %s" % regexp)
