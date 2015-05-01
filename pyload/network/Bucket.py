# -*- coding: utf-8 -*-
# @author: RaNaN

import threading

from time import time


MIN_RATE = 10240  #: 10kb minimum rate


class Bucket(object):

    def __init__(self):
        self.rate      = 0  #: bytes per second, maximum targeted throughput
        self.tokens    = 0
        self.timestamp = time()
        self.lock      = threading.Lock()


    def __nonzero__(self):
        return self.rate >= MIN_RATE


    def setRate(self, rate):
        self.lock.acquire()
        self.rate = int(rate)
        self.lock.release()


    def consumed(self, amount):
        """ return the time the process has to sleep, after it consumed a specified amount """
        if self.rate < MIN_RATE:
            return 0  #: May become unresponsive otherwise

        self.lock.acquire()
        self.calc_tokens()
        self.tokens -= amount

        time = -self.tokens / float(self.rate) if self.tokens < 0 else 0

        self.lock.release()
        return time


    def calc_tokens(self):
        if self.tokens < self.rate:
            now = time()
            delta = self.rate * (now - self.timestamp)
            self.tokens = min(self.rate, self.tokens + delta)
            self.timestamp = now
