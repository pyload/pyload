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

    @author: Walter Purcaro
"""

from module.plugins.Hook import Hook
from re import search


class ChunkControl(Hook):
    __name__ = "ChunkControl"
    __version__ = "0.03"
    __description__ = "Define chunks number"
    __config__ = [
        ("activated", "bool", "Activated", "False"),
        ("premium", "int", "Premium: Default chunks number", "1"),
        ("free", "int", "Free: Default chunks number", "1"),
        ("hosters", "str", "Set chunks number for hoster as \"hostername F# P#\" (comma separated)", "")
    ]
    __author_name__ = ("Walter Purcaro")
    __author_mail__ = ("vuolter@gmail.com")

    event_map = {"downloadStarts": "downloadStarts"}

    def getChunks(self, pluginname="baseplugin", premium=False, hosters=[]):
        for hoster in hosters:
            rules = hoster.lower().split()
            if rules[0].strip() == pluginname.lower():
                rules.pop(0)
                for rule in rules:
                    rule = rule.strip()
                    if (rule.startswith("p") and premium) or (rule.startswith("f") and not premium):
                        res = search('(\d+)', rule)
                    else:
                        continue
                    if res:
                        return int(res.group(0))
                    else:
                        break
        return self.getConfig("premium") if premium else self.getConfig("free")

    def syncSetting(self, coresync=False):
        now = self.config["download"]["chunks"]
        last = self.info["last"]
        if now != last:
            self.logDebug("detected core chunks setting was changed: store newer")
            self.info["orig"] = now
        if coresync:
            self.config["download"]["chunks"] = self.info["orig"]

    def downloadStarts(self, pyfile, url, filename):
        premium = pyfile.plugin.premium
        hosters = self.getConfig("hosters")
        if hosters:
            hosters = hosters.replace('|', ',').replace(';', ',').split(',')
            self.logDebug("overwrited default rules with %s" % hosters)
        self.syncSetting()
        chunks = self.getChunks(pyfile.pluginname, premium, hosters)
        self.config["download"]["chunks"] = self.info["last"] = chunks
        self.logInfo("download file using %s chunks" % chunks)

    def unload(self):
        self.syncSetting(True)

    def coreReady(self):
        chunks = self.config["download"]["chunks"]
        self.info = {"orig": chunks, "last": chunks}

    def setup(self):
        self.config = self.core.config
