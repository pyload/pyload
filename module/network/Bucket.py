#!/usr/bin/env python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
#@author: RaNaN



from builtins import object

from time import time
from threading import Lock

class Bucket(object):
    def __init__(self):
        self.rate = 0
        self.tokens = 0
        self.timestamp = time()
        self.lock = Lock()

    def __bool__(self):
        return False if self.rate < 10240 else True

    def setRate(self, rate):
        self.lock.acquire()
        self.rate = int(rate)
        self.lock.release()

    def consumed(self, amount):
        """ return time the process have to sleep, after consumed specified amount """
        if self.rate < 10240: return 0 #min. 10kb, may become unresponsive otherwise
        self.lock.acquire()

        self.calc_tokens()
        self.tokens -= amount

        if self.tokens < 0:
            time = -self.tokens / self.rate
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

