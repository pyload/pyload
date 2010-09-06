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

from time import sleep
from Queue import Queue
from threading import Thread

class Scheduler():
    def __init__(self, core):
        self.core = core
        
        self.queue = Queue()
    
    def addJob(self, time, call, args=[], kwargs={}, done=None):
        j = Job(time, call, args, kwargs, done)
        self.queue.put(j)

class Job(Thread):
    def __init__(self, time, call, args=[], kwargs={}, done=None):
        Thread.__init__(self)
        self.time = float(time)
        self.interval = 0.5
        self.call = call
        self.done = done
        self.args = args
        self.kwargs = kwargs
    
    def run(self):
        while self.time > 0:
            sleep(self.interval)
            self.time -= self.interval
        self.work()
    
    def work(self):
        ret = self.call(*self.args, **self.kwargs)
        if self.done is None:
            return
        if ret is None:
            self.done()
        else:
            self.done(ret)
