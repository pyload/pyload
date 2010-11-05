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

from time import time
from heapq import heappop, heappush
from threading import Thread, Lock

class AlreadyCalled(Exception):
    pass

def callInThread(f, *args, **kwargs):
    class FThread(Thread):
        def run(self):
            f(*args, **kwargs)
    t = FThread()
    t.start()

class Deferred():
    def __init__(self):
        self.call = []
        self.result = ()
    
    def addCallback(self, f, *cargs, **ckwargs):
        self.call.append((f, cargs, ckwargs))
        if self.result:
            args, kwargs = self.result
            args.extend(cargs)
            kwargs.update(ckwargs)
            callInThread(f, *args, **kwargs)
    
    def callback(self, *args, **kwargs):
        if self.result:
            raise AlreadyCalled
        self.result = (args, kwargs)
        for f, cargs, ckwargs in self.call:
            args+=tuple(cargs)
            kwargs.update(ckwargs)
            callInThread(f, *args, **kwargs)

class Scheduler():
    def __init__(self, core):
        self.core = core
        
        self.queue = PriorityQueue()
    
    def addJob(self, t, call, args=[], kwargs={}):
        d = Deferred()
        t += time()
        j = Job(t, call, args, kwargs, d)
        self.queue.put((t, j))
        return d
    
    def work(self):
        while True:
            t, j = self.queue.get()
            if not j:
                break
            else:
                if t <= time():
                    j.start()
                else:
                    self.queue.put((t, j))
                    break

class Job(Thread):
    def __init__(self, time, call, args=[], kwargs={}, deferred=None):
        Thread.__init__(self)
        self.time = float(time)
        self.call = call
        self.deferred = deferred
        self.args = args
        self.kwargs = kwargs
    
    def run(self):
        ret = self.call(*self.args, **self.kwargs)
        if self.deferred is None:
            return
        if ret is None:
            self.deferred.callback()
        else:
            self.deferred.callback(ret)


class PriorityQueue():
    """ a non blocking priority queue """
    def __init__(self):
        self.queue = []
        self.lock = Lock()

    def put(self, element):
        self.lock.acquire()
        heappush(self.queue, element)
        self.lock.release()

    def get(self):
        """ return element or None """
        self.lock.acquire()
        try:
            el = heappop(self.queue)
            return el
        except IndexError:
            return None,None
        finally:
            self.lock.release()