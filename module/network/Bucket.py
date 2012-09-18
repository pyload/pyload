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
    
    @author: RaNaN
"""

from time import time
from threading import Lock

# 10kb minimum rate
MIN_RATE = 10240

class Bucket:
    def __init__(self):
        self.rate = 0 # bytes per second, maximum targeted throughput
        self.tokens = 0
        self.timestamp = time()
        self.lock = Lock()

    def __nonzero__(self):
        return False if self.rate < MIN_RATE else True

    def setRate(self, rate):
        self.lock.acquire()
        self.rate = int(rate)
        self.lock.release()

    def consumed(self, amount):
        """ return the time the process has to sleep, after it consumed a specified amount """
        if self.rate < MIN_RATE: return 0 #May become unresponsive otherwise
        self.lock.acquire()

        self.calc_tokens()
        self.tokens -= amount

        if self.tokens < 0:
            time = -self.tokens/float(self.rate)
        else:
            time = 0

        self.lock.release()
        return time

    def calc_tokens(self):
        if self.tokens < self.rate:
            now = time()
            delta = self.rate * (now - self.timestamp)
            self.tokens = min(self.rate, self.tokens + delta)
            self.timestamp = now

