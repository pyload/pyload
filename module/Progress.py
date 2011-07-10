#!/usr/bin/env python
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

    @author: mkaay
"""

class Progress:
    def __init__(self, maximum=0, minimum=100):
        self.maximum = maximum
        self.minimum = minimum
        self.value = 0
        self.notify = None
    
    def setRange(self, maximum, minimum):
        self.maximum = maximum
        self.minimum = minimum
    
    def setValue(self, value):
        if not value == self.value:
            self.value = value
            if self.notify:
                self.notify()
    
    def getPercent(self):
        try:
            return int(self.value)
        except:
            return 0
