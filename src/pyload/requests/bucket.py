# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import time
from builtins import int, object

from future import standard_library

standard_library.install_aliases()


class Bucket(object):

    __slots__ = ['_rate', 'timestamp', 'token']

    MIN_RATE = 10240  # 10kb minimum rate

    def __init__(self):
        self._rate = 0  # bytes per second, maximum targeted throughput
        self.token = 0
        self.timestamp = time.time()

    def __bool__(self):
        return self.rate >= self.MIN_RATE

    def get_rate(self):
        return self._rate

    def set_rate(self, rate):
        self._rate = int(rate)

    rate = property(get_rate, set_rate)

    def _calc_token(self):
        if self.token >= self.rate:
            return None
        now = time.time()
        delta = self.rate * (now - self.timestamp)
        self.token = min(self.rate, self.token + delta)
        self.timestamp = now

    def consumed(self, amount):
        """
        Return the time the process has to sleep,
        after it consumed a specified amount
        """
        if self.rate < self.MIN_RATE:
            return 0  # NOTE: May become unresponsive otherwise
        self._calc_token()
        self.token -= amount
        consumed = -self.token // float(self.rate) if self.token < 0 else 0
        return consumed
