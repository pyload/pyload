#!/usr/bin/env python
# -*- coding: utf-8 -*-
#@author: mkaay



from builtins import object
from time import time
from heapq import heappop, heappush
from _thread import start_new_thread
from threading import Lock

class AlreadyCalled(Exception):
    pass


class Deferred(object):
    def __init__(self):
        self.call = []
        self.result = ()

    def addCallback(self, f, *cargs, **ckwargs):
        self.call.append((f, cargs, ckwargs))

    def callback(self, *args, **kwargs):
        if self.result:
            raise AlreadyCalled
        self.result = (args, kwargs)
        for f, cargs, ckwargs in self.call:
            args += tuple(cargs)
            kwargs.update(ckwargs)
            f(*args ** kwargs)


class Scheduler(object):
    def __init__(self, core):
        self.core = core

        self.queue = PriorityQueue()

    def addJob(self, t, call, args=[], kwargs={}, threaded=True):
        d = Deferred()
        t += time()
        j = Job(t, call, args, kwargs, d, threaded)
        self.queue.put((t, j))
        return d


    def removeJob(self, d):
        """
        :param d: defered object
        :return: if job was deleted
        """
        index = -1

        for i, j in enumerate(self.queue):
            if j[1].deferred == d:
                index = i

        if index >= 0:
            del self.queue[index]
            return True

        return False

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


class Job(object):
    def __init__(self, time, call, args=[], kwargs={}, deferred=None, threaded=True):
        self.time = float(time)
        self.call = call
        self.args = args
        self.kwargs = kwargs
        self.deferred = deferred
        self.threaded = threaded

    def run(self):
        ret = self.call(*self.args, **self.kwargs)
        if self.deferred is None:
            return
        else:
            self.deferred.callback(ret)

    def start(self):
        if self.threaded:
            start_new_thread(self.run, ())
        else:
            self.run()


class PriorityQueue(object):
    """ a non blocking priority queue """

    def __init__(self):
        self.queue = []
        self.lock = Lock()

    def __iter__(self):
        return iter(self.queue)

    def __delitem__(self, key):
        del self.queue[key]

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
            return None, None
        finally:
            self.lock.release()