# -*- coding: utf-8 -*-
# @author: RaNaN

from time import time
from threading import Lock

MIN_RATE = 10240  #: 10kb minimum rate


class Bucket(object):

    def __init__(self):
        self.rate      = 0  #: bytes per second, maximum targeted throughput
        self.tokens    = 0
        self.timestamp = time()
        self.lock      = Lock()


    def __nonzero__(self):
        return False if self.rate < MIN_RATE else True


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
