# -*- coding: utf-8 -*-

"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.

    @author: zoidberg
"""
from __future__ import unicode_literals

import re

from pyload.plugins.Hook import Hook
from pyload.network.RequestFactory import getURL
from pyload.utils import remove_chars


class LinkdecrypterCom(Hook):
    __name__ = "LinkdecrypterCom"
    __version__ = "0.19"
    __description__ = """Linkdecrypter.com hook plugin"""
    __config__ = [("activated", "bool", "Activated", False)]
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"

    def coreReady(self):
        try:
            self.loadPatterns()
        except Exception as e:
            self.logError(e)

    def loadPatterns(self):
        page = getURL("http://linkdecrypter.com/")
        m = re.search(r'<b>Supported\(\d+\)</b>: <i>([^+<]*)', page)
        if not m:
            self.logError(_("Crypter list not found"))
            return

        builtin = [name.lower() for name in list(self.core.pluginManager.crypterPlugins.keys())]
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

        dict = self.core.pluginManager.crypterPlugins[self.__name__]
        dict["pattern"] = regexp
        dict["re"] = re.compile(regexp)

        self.logDebug("REGEXP: " + regexp)
