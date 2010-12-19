#!/usr/bin/env python
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
    
    @author: mkaay
"""

from time import time, sleep
from threading import Lock

class Bucket:
    def __init__(self):
        self.tokens = 0
        self.rate = 0
        self.lastDrip = time()
        self.lock = Lock()
    
    def setRate(self, rate):
        self.lock.acquire()
        self.rate = rate
        self.lock.release()
    
    def consume(self, amount):
        """ consume specified amount, return False if not enough tokens in bucket """
        if not self.rate: return True
        self.lock.acquire()
        if amount < self.getTokens():
            self.tokens -= amount
            self.lock.release()
            return True

        self.lock.release()
        return False

    def getTokens(self):
        if self.tokens < self.rate:
            now = time()
            delta = self.rate * (now - self.lastDrip)
            self.tokens = min(self.rate, self.tokens + delta)
            self.lastDrip = now
        return self.tokens
