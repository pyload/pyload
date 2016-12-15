# -*- coding: utf-8 -*-
#@author: zoidberg

from __future__ import unicode_literals

import re

from pyload.plugins.hook import Hook
from pyload.network.requestfactory import get_url
from pyload.utils import remove_chars


class LinkdecrypterCom(Hook):
    __name__ = "LinkdecrypterCom"
    __version__ = "0.19"
    __description__ = """Linkdecrypter.com hook plugin"""
    __config__ = [("activated", "bool", "Activated", False)]
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"

    def core_ready(self):
        try:
            self.loadPatterns()
        except Exception as e:
            self.logError(e)

    def load_patterns(self):
        page = get_url("http://linkdecrypter.com/")
        m = re.search(r'<b>Supported\(\d+\)</b>: <i>([^+<]*)', page)
        if not m:
            self.logError(_("Crypter list not found"))
            return

        builtin = [name.lower() for name in self.pyload.pluginmanager.crypterPlugins.keys()]
        builtin.extend(["downloadserienjunkiesorg"])

        crypter_pattern = re.compile("(\w[\w.-]+)")
        online = []
        for crypter in m.group(1).split(', '):
            m = re.match(crypter_pattern, crypter)
            if m and remove_chars(m.group(1), "-.") not in builtin:
                online.append(m.group(1).replace(".", "\\."))

        if not online:
            self.logError(_("Crypter list is empty"))
            return

        regexp = r"https?://([^.]+\.)*?(%s)/.*" % "|".join(online)

        dict = self.pyload.pluginmanager.crypterPlugins[self.__name__]
        dict["pattern"] = regexp
        dict["re"] = re.compile(regexp)

        self.logDebug("REGEXP: " + regexp)
