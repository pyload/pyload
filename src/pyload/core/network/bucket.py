# -*- coding: utf-8 -*-

import time
from threading import Lock

from ..utils.struct.lock import lock


class Bucket:

    MIN_RATE = 10 << 10  # 10kb minimum rate

    def __init__(self):
        self._rate = 0
        self.token = 0
        self.timestamp = time.time()
        self.lock = Lock()

    def __bool__(self):
        return self._rate >= self.MIN_RATE

    @lock
    def set_rate(self, rate):
        self._rate = int(rate)

    def get_rate(self):
        return self._rate

    rate = property(get_rate, set_rate)

    def _calc_token(self):
        if self.token >= self._rate:
            return
        now = time.time()
        delta = self._rate * (now - self.timestamp)
        self.token = min(self._rate, self.token + delta)
        self.timestamp = now

    @lock
    def consumed(self, amount):
        """
        Return time the process have to sleep, after consumed specified amount.
        """
        if self.rate < self.MIN_RATE:
            return 0  # NOTE: May become unresponsive otherwise
        self._calc_token()
        self.token -= amount
        consumed = -self.token // self._rate if self.token < 0 else 0
        return consumed
