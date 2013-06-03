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
    __version__ = "0.01"
    __description__ = "Define chunks number according to the rules"
    __config__ = [
        ("activated", "bool", "Activated", "False"),
        ("premium", "int", "Chunks number for premium downloads", "1"),
        ("free", "int", "Chunks number for free downloads", "1"),
        ("hosters", "str", "List chunks number for hoster as hostername F# P# (comma separated)", "")
    ]
    __author_name__ = ("Walter Purcaro")
    __author_mail__ = ("vuolter@gmail.com")

    def getChunks(self, hosters, premium):
        for hoster in hosters:
            rules = hoster.lower().split()
            if rules[0].strip() == pyfile.pluginname:
                for rule in xrange(1, len(rules)):
                    rule.strip()
                    if (rule.startswith("p") and premium)
                    or (rule.startswith("f") and not premium):
                        chunks = search(r'\d+', rule)
                    else:
                        continue
                    return chunks if chunks else break
        return self.getConf("premium") if premium else self.getConf("free")

    def downloadStarts(self, pyfile, url, filename):
        premium = pyfile.premium
        chunks = self.config["download"]["chunks"]
        chunkslast = self.info["last"]
        if chunks != chunkslast:
            self.info["orig"] = chunks
        hosters = self.getConf("hosters", "").replace('|', ',').replace(';', ',').split(',')
        chunks = self.getChunks(hosters, premium)
        self.config["download"]["chunks"] = self.info["last"] = chunks

    def unload(self):
        self.config["download"]["chunks"] = self.info["orig"]

    def coreReady(self):
        chunks = self.core.config["download"]["chunks"]
        self.info = {"orig": chunks, "last": chunks}
