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
from time import time


class DeleteFinished(Hook):
    __name__ = "DeleteFinished"
    __version__ = "0.2"
    __description__ = "Automatically delete finished packages from queue"
    __config__ = [
        ("activated", "bool", "Activated", "False"),
        ("interval", "int", "Delete every (hours)", "72")
    ]
    __author_name__ = ("Walter Purcaro")
    __author_mail__ = ("vuolter@gmail.com")

    #: event_map don't load periodical anyway
    def periodical(self):
        now = time()
        deletetime = self.getConfig("interval") * 3600 + self.info["lastdelete"]
        if now >= deletetime:
            self.core.api.deleteFinished()
            self.logDebug("called self.core.api.deleteFinished()")
            self.info["lastdelete"] = now

    def setup(self):
        now = time()
        self.info = {"lastdelete": now}
        self.interval = 3600
