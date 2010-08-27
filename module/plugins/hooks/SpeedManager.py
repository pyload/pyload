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

    @author: RaNaN
    @interface-version: 0.1
"""

from module.plugins.Hook import Hook
from module.SpeedManager import SpeedManager as SpeedHandler

class SpeedManager(Hook):
    __name__ = "SpeedManager"
    __version__ = "0.1"
    __description__ = """Limiting the speed if needed"""
    __config__ = [("activated", "bool", "Activated", "False"),
                  ("speed", "int", "Speedlimit in kb/s", "500"),
                  ("start", "str", "Start-time of speed limiting", "0:00"),
                  ("end", "str", "End-time of speed limiting", "0:00")]
    __author_name__ = ("RaNaN")
    __author_mail__ = ("ranan@pyload.org")

    def coreReady(self):
        self.speedManager = SpeedHandler(self.core, self)
        self.core.log.debug("SpeedManager started")
        #@TODO start speed manager when needed