# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, unicode_literals

from builtins import int, object
from time import time

from future import standard_library

standard_library.install_aliases()

# 10kb minimum rate
MIN_RATE = 10240


class Bucket(object):

    __slots__ = ['rate', 'timestamp', 'tokens']

    def __init__(self):
        self.rate = 0  #: bytes per second, maximum targeted throughput
        self.tokens = 0
        self.timestamp = time()

    def __bool__(self):
        return False if self.rate < MIN_RATE else True

    def set_rate(self, rate):
        self.rate = int(rate)

    def consumed(self, amount):
        """
        Return the time the process has to sleep, after it consumed a specified amount.
        """
        if self.rate < MIN_RATE:
            return 0  #: May become unresponsive otherwise

        self.calc_tokens()
        self.tokens -= amount

        if self.tokens < 0:
            return -self.tokens // float(self.rate)
        else:
            return 0

    def calc_tokens(self):
        if self.tokens < self.rate:
            now = time()
            delta = self.rate * (now - self.timestamp)
            self.tokens = min(self.rate, self.tokens + delta)
            self.timestamp = now
